#include <windows.h>
#include <shlobj.h>
#include <shlwapi.h>

#include <algorithm>
#include <atomic>
#include <cwctype>
#include <filesystem>
#include <new>
#include <string>
#include <utility>
#include <vector>

#include "generated_actions.h"

#pragma comment(lib, "Ole32.lib")
#pragma comment(lib, "Shell32.lib")
#pragma comment(lib, "Shlwapi.lib")

namespace {

const CLSID CLSID_UwUConverterCommand = {
    0x8460e4fc,
    0xb85d,
    0x4a8a,
    {0xa6, 0x62, 0xc6, 0xff, 0x3d, 0x7c, 0x47, 0x27},
};

HMODULE g_module = nullptr;
std::atomic<long> g_objectCount{0};
std::atomic<long> g_lockCount{0};

std::wstring ToLower(std::wstring value) {
    std::transform(
        value.begin(),
        value.end(),
        value.begin(),
        [](wchar_t ch) { return static_cast<wchar_t>(std::towlower(ch)); }
    );
    return value;
}

std::wstring ModulePath() {
    std::wstring buffer(MAX_PATH, L'\0');

    for (;;) {
        DWORD written = GetModuleFileNameW(
            g_module,
            buffer.data(),
            static_cast<DWORD>(buffer.size())
        );

        if (written == 0) {
            return {};
        }

        if (written < buffer.size() - 1) {
            buffer.resize(written);
            return buffer;
        }

        buffer.resize(buffer.size() * 2);
    }
}

std::filesystem::path AppDirectory() {
    std::filesystem::path dllPath(ModulePath());
    return dllPath.parent_path().parent_path();
}

std::wstring QuoteArgument(const std::wstring& value) {
    if (value.empty()) {
        return L"\"\"";
    }

    if (value.find_first_of(L" \t\n\v\"") == std::wstring::npos) {
        return value;
    }

    std::wstring result = L"\"";
    size_t backslashes = 0;

    for (wchar_t ch : value) {
        if (ch == L'\\') {
            ++backslashes;
            continue;
        }

        if (ch == L'\"') {
            result.append(backslashes * 2 + 1, L'\\');
            result.push_back(L'\"');
            backslashes = 0;
            continue;
        }

        result.append(backslashes, L'\\');
        backslashes = 0;
        result.push_back(ch);
    }

    result.append(backslashes * 2, L'\\');
    result.push_back(L'\"');
    return result;
}

bool ExtensionListContains(const wchar_t* list, const std::wstring& extension) {
    if (!list || !*list || extension.empty()) {
        return false;
    }

    std::wstring needle = ToLower(extension);
    std::wstring all = ToLower(list);
    size_t start = 0;

    while (start <= all.size()) {
        size_t end = all.find(L';', start);
        std::wstring item = all.substr(
            start,
            end == std::wstring::npos ? std::wstring::npos : end - start
        );

        if (item == needle) {
            return true;
        }

        if (end == std::wstring::npos) {
            break;
        }

        start = end + 1;
    }

    return false;
}

struct SelectedItem {
    std::wstring path;
    std::wstring extension;
    bool isFolder = false;
};

HRESULT ReadSelection(IShellItemArray* items, std::vector<SelectedItem>& output) {
    output.clear();

    if (!items) {
        return E_INVALIDARG;
    }

    DWORD count = 0;
    HRESULT hr = items->GetCount(&count);

    if (FAILED(hr)) {
        return hr;
    }

    for (DWORD index = 0; index < count; ++index) {
        IShellItem* item = nullptr;
        hr = items->GetItemAt(index, &item);

        if (FAILED(hr) || !item) {
            continue;
        }

        PWSTR rawPath = nullptr;
        hr = item->GetDisplayName(SIGDN_FILESYSPATH, &rawPath);

        if (SUCCEEDED(hr) && rawPath) {
            SelectedItem selected;
            selected.path = rawPath;

            // Explorer can expose archive files (especially .zip) with the
            // SFGAO_FOLDER shell attribute because they are browsable like
            // folders. That does not make them filesystem directories.
            //
            // Use filesystem attributes instead so archive files keep their
            // extension and get extraction actions, while Batch Convert Folder
            // remains limited to actual directories.
            DWORD fileAttributes = GetFileAttributesW(rawPath);

            selected.isFolder =
                fileAttributes != INVALID_FILE_ATTRIBUTES &&
                (fileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0;

            if (!selected.isFolder) {
                const wchar_t* extension = PathFindExtensionW(rawPath);
                selected.extension = ToLower(extension ? extension : L"");
            }

            output.push_back(std::move(selected));
        }

        CoTaskMemFree(rawPath);
        item->Release();
    }

    return output.empty() ? E_FAIL : S_OK;
}

bool ActionApplies(
    const UwUActionDefinition& action,
    const std::vector<SelectedItem>& selection
) {
    if (action.folderOnly) {
        return selection.size() == 1 && selection[0].isFolder;
    }

    for (const auto& item : selection) {
        if (!item.isFolder && ExtensionListContains(action.extensions, item.extension)) {
            return true;
        }
    }

    return false;
}

std::vector<std::wstring> PathsForAction(
    const UwUActionDefinition& action,
    const std::vector<SelectedItem>& selection
) {
    std::vector<std::wstring> paths;

    if (action.folderOnly) {
        if (selection.size() == 1 && selection[0].isFolder) {
            paths.push_back(selection[0].path);
        }
        return paths;
    }

    for (const auto& item : selection) {
        if (!item.isFolder && ExtensionListContains(action.extensions, item.extension)) {
            paths.push_back(item.path);
        }
    }

    return paths;
}

HRESULT LaunchAction(
    const UwUActionDefinition& action,
    const std::vector<std::wstring>& paths
) {
    if (paths.empty()) {
        return E_INVALIDARG;
    }

    std::filesystem::path executable = AppDirectory() / L"UwUConverter.exe";

    if (!std::filesystem::is_regular_file(executable)) {
        return HRESULT_FROM_WIN32(ERROR_FILE_NOT_FOUND);
    }

    std::wstring commandLine = QuoteArgument(executable.wstring());

    if (action.folderOnly) {
        commandLine += L" ";
        commandLine += QuoteArgument(paths.front());
        commandLine += L" ";
        commandLine += QuoteArgument(action.action);
    } else {
        commandLine += L" __MULTI__ ";
        commandLine += QuoteArgument(action.action);

        for (const auto& path : paths) {
            commandLine += L" ";
            commandLine += QuoteArgument(path);
        }
    }

    std::vector<wchar_t> mutableCommand(
        commandLine.begin(),
        commandLine.end()
    );
    mutableCommand.push_back(L'\0');

    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process{};

    BOOL created = CreateProcessW(
        executable.c_str(),
        mutableCommand.data(),
        nullptr,
        nullptr,
        FALSE,
        CREATE_UNICODE_ENVIRONMENT,
        nullptr,
        AppDirectory().c_str(),
        &startup,
        &process
    );

    if (!created) {
        return HRESULT_FROM_WIN32(GetLastError());
    }

    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return S_OK;
}

class ActionCommand final : public IExplorerCommand {
public:
    explicit ActionCommand(const UwUActionDefinition* definition)
        : definition_(definition) {
        ++g_objectCount;
    }

    ~ActionCommand() {
        --g_objectCount;
    }

    IFACEMETHODIMP QueryInterface(REFIID iid, void** object) override {
        if (!object) {
            return E_POINTER;
        }

        *object = nullptr;

        if (iid == IID_IUnknown || iid == IID_IExplorerCommand) {
            *object = static_cast<IExplorerCommand*>(this);
            AddRef();
            return S_OK;
        }

        return E_NOINTERFACE;
    }

    IFACEMETHODIMP_(ULONG) AddRef() override {
        return static_cast<ULONG>(InterlockedIncrement(&references_));
    }

    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG value = static_cast<ULONG>(InterlockedDecrement(&references_));
        if (value == 0) {
            delete this;
        }
        return value;
    }

    IFACEMETHODIMP GetTitle(IShellItemArray*, PWSTR* title) override {
        if (!title) {
            return E_POINTER;
        }
        return SHStrDupW(definition_->title, title);
    }

    IFACEMETHODIMP GetIcon(IShellItemArray*, PWSTR* icon) override {
        if (!icon) {
            return E_POINTER;
        }

        std::wstring value = (AppDirectory() / L"UwUConverter.exe").wstring();
        value += L",0";
        return SHStrDupW(value.c_str(), icon);
    }

    IFACEMETHODIMP GetToolTip(IShellItemArray*, PWSTR* tooltip) override {
        if (tooltip) {
            *tooltip = nullptr;
        }
        return E_NOTIMPL;
    }

    IFACEMETHODIMP GetCanonicalName(GUID* canonicalName) override {
        if (!canonicalName) {
            return E_POINTER;
        }
        *canonicalName = GUID_NULL;
        return S_OK;
    }

    IFACEMETHODIMP GetState(
        IShellItemArray* items,
        BOOL,
        EXPCMDSTATE* state
    ) override {
        if (!state) {
            return E_POINTER;
        }

        std::vector<SelectedItem> selection;
        if (FAILED(ReadSelection(items, selection))) {
            *state = ECS_HIDDEN;
            return S_OK;
        }

        *state = ActionApplies(*definition_, selection)
            ? ECS_ENABLED
            : ECS_HIDDEN;
        return S_OK;
    }

    IFACEMETHODIMP Invoke(IShellItemArray* items, IBindCtx*) override {
        std::vector<SelectedItem> selection;
        HRESULT hr = ReadSelection(items, selection);
        if (FAILED(hr)) {
            return hr;
        }

        return LaunchAction(
            *definition_,
            PathsForAction(*definition_, selection)
        );
    }

    IFACEMETHODIMP GetFlags(EXPCMDFLAGS* flags) override {
        if (!flags) {
            return E_POINTER;
        }
        *flags = ECF_DEFAULT;
        return S_OK;
    }

    IFACEMETHODIMP EnumSubCommands(IEnumExplorerCommand** commands) override {
        if (commands) {
            *commands = nullptr;
        }
        return E_NOTIMPL;
    }

private:
    LONG references_ = 1;
    const UwUActionDefinition* definition_;
};

class CommandEnumerator final : public IEnumExplorerCommand {
public:
    CommandEnumerator() {
        ++g_objectCount;

        commands_.reserve(kUwUActionCount);
        for (size_t index = 0; index < kUwUActionCount; ++index) {
            auto* command = new (std::nothrow) ActionCommand(&kUwUActions[index]);
            if (command) {
                commands_.push_back(command);
            }
        }
    }

    ~CommandEnumerator() {
        for (IExplorerCommand* command : commands_) {
            command->Release();
        }
        --g_objectCount;
    }

    IFACEMETHODIMP QueryInterface(REFIID iid, void** object) override {
        if (!object) {
            return E_POINTER;
        }

        *object = nullptr;
        if (iid == IID_IUnknown || iid == IID_IEnumExplorerCommand) {
            *object = static_cast<IEnumExplorerCommand*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }

    IFACEMETHODIMP_(ULONG) AddRef() override {
        return static_cast<ULONG>(InterlockedIncrement(&references_));
    }

    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG value = static_cast<ULONG>(InterlockedDecrement(&references_));
        if (value == 0) {
            delete this;
        }
        return value;
    }

    IFACEMETHODIMP Next(
        ULONG count,
        IExplorerCommand** commands,
        ULONG* fetched
    ) override {
        if (!commands) {
            return E_POINTER;
        }

        if (count != 1 && !fetched) {
            return E_POINTER;
        }

        ULONG produced = 0;

        while (produced < count && index_ < commands_.size()) {
            commands[produced] = commands_[index_];
            commands[produced]->AddRef();
            ++produced;
            ++index_;
        }

        if (fetched) {
            *fetched = produced;
        }

        return produced == count ? S_OK : S_FALSE;
    }

    IFACEMETHODIMP Skip(ULONG count) override {
        size_t remaining = commands_.size() - index_;
        size_t skipped = std::min<size_t>(count, remaining);
        index_ += skipped;
        return skipped == count ? S_OK : S_FALSE;
    }

    IFACEMETHODIMP Reset() override {
        index_ = 0;
        return S_OK;
    }

    IFACEMETHODIMP Clone(IEnumExplorerCommand** clone) override {
        if (!clone) {
            return E_POINTER;
        }

        auto* copy = new (std::nothrow) CommandEnumerator();
        if (!copy) {
            return E_OUTOFMEMORY;
        }

        copy->index_ = index_;
        *clone = copy;
        return S_OK;
    }

private:
    LONG references_ = 1;
    size_t index_ = 0;
    std::vector<IExplorerCommand*> commands_;
};

class RootCommand final : public IExplorerCommand {
public:
    RootCommand() {
        ++g_objectCount;
    }

    ~RootCommand() {
        --g_objectCount;
    }

    IFACEMETHODIMP QueryInterface(REFIID iid, void** object) override {
        if (!object) {
            return E_POINTER;
        }

        *object = nullptr;
        if (iid == IID_IUnknown || iid == IID_IExplorerCommand) {
            *object = static_cast<IExplorerCommand*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }

    IFACEMETHODIMP_(ULONG) AddRef() override {
        return static_cast<ULONG>(InterlockedIncrement(&references_));
    }

    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG value = static_cast<ULONG>(InterlockedDecrement(&references_));
        if (value == 0) {
            delete this;
        }
        return value;
    }

    IFACEMETHODIMP GetTitle(IShellItemArray*, PWSTR* title) override {
        if (!title) {
            return E_POINTER;
        }
        return SHStrDupW(L"UwUConverter", title);
    }

    IFACEMETHODIMP GetIcon(IShellItemArray*, PWSTR* icon) override {
        if (!icon) {
            return E_POINTER;
        }

        std::wstring value = (AppDirectory() / L"UwUConverter.exe").wstring();
        value += L",0";
        return SHStrDupW(value.c_str(), icon);
    }

    IFACEMETHODIMP GetToolTip(IShellItemArray*, PWSTR* tooltip) override {
        if (tooltip) {
            *tooltip = nullptr;
        }
        return E_NOTIMPL;
    }

    IFACEMETHODIMP GetCanonicalName(GUID* canonicalName) override {
        if (!canonicalName) {
            return E_POINTER;
        }
        *canonicalName = CLSID_UwUConverterCommand;
        return S_OK;
    }

    IFACEMETHODIMP GetState(
        IShellItemArray* items,
        BOOL,
        EXPCMDSTATE* state
    ) override {
        if (!state) {
            return E_POINTER;
        }

        std::vector<SelectedItem> selection;
        if (FAILED(ReadSelection(items, selection))) {
            *state = ECS_HIDDEN;
            return S_OK;
        }

        for (size_t index = 0; index < kUwUActionCount; ++index) {
            if (ActionApplies(kUwUActions[index], selection)) {
                *state = ECS_ENABLED;
                return S_OK;
            }
        }

        *state = ECS_HIDDEN;
        return S_OK;
    }

    IFACEMETHODIMP Invoke(IShellItemArray*, IBindCtx*) override {
        return E_NOTIMPL;
    }

    IFACEMETHODIMP GetFlags(EXPCMDFLAGS* flags) override {
        if (!flags) {
            return E_POINTER;
        }
        *flags = ECF_HASSUBCOMMANDS;
        return S_OK;
    }

    IFACEMETHODIMP EnumSubCommands(IEnumExplorerCommand** commands) override {
        if (!commands) {
            return E_POINTER;
        }

        *commands = new (std::nothrow) CommandEnumerator();
        return *commands ? S_OK : E_OUTOFMEMORY;
    }

private:
    LONG references_ = 1;
};

class CommandFactory final : public IClassFactory {
public:
    CommandFactory() {
        ++g_objectCount;
    }

    ~CommandFactory() {
        --g_objectCount;
    }

    IFACEMETHODIMP QueryInterface(REFIID iid, void** object) override {
        if (!object) {
            return E_POINTER;
        }

        *object = nullptr;
        if (iid == IID_IUnknown || iid == IID_IClassFactory) {
            *object = static_cast<IClassFactory*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }

    IFACEMETHODIMP_(ULONG) AddRef() override {
        return static_cast<ULONG>(InterlockedIncrement(&references_));
    }

    IFACEMETHODIMP_(ULONG) Release() override {
        ULONG value = static_cast<ULONG>(InterlockedDecrement(&references_));
        if (value == 0) {
            delete this;
        }
        return value;
    }

    IFACEMETHODIMP CreateInstance(
        IUnknown* outer,
        REFIID iid,
        void** object
    ) override {
        if (outer) {
            return CLASS_E_NOAGGREGATION;
        }

        auto* command = new (std::nothrow) RootCommand();
        if (!command) {
            return E_OUTOFMEMORY;
        }

        HRESULT hr = command->QueryInterface(iid, object);
        command->Release();
        return hr;
    }

    IFACEMETHODIMP LockServer(BOOL lock) override {
        if (lock) {
            ++g_lockCount;
        } else {
            --g_lockCount;
        }
        return S_OK;
    }

private:
    LONG references_ = 1;
};

}  // namespace

extern "C" BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        g_module = instance;
        DisableThreadLibraryCalls(instance);
    }
    return TRUE;
}

extern "C" HRESULT __stdcall DllCanUnloadNow() {
    return (g_objectCount.load() == 0 && g_lockCount.load() == 0)
        ? S_OK
        : S_FALSE;
}

extern "C" HRESULT __stdcall DllGetClassObject(
    REFCLSID clsid,
    REFIID iid,
    void** object
) {
    if (!object) {
        return E_POINTER;
    }

    *object = nullptr;

    if (!IsEqualCLSID(clsid, CLSID_UwUConverterCommand)) {
        return CLASS_E_CLASSNOTAVAILABLE;
    }

    auto* factory = new (std::nothrow) CommandFactory();
    if (!factory) {
        return E_OUTOFMEMORY;
    }

    HRESULT hr = factory->QueryInterface(iid, object);
    factory->Release();
    return hr;
}
