import pathlib

import trimesh

MODEL_OUTPUTS = {
    "obj",
    "stl",
    "ply",
    "glb",
}

def convert_model(
    file_path,
    output_file_path,
    output_format
):
    output_format = output_format.lower()

    if output_format not in MODEL_OUTPUTS:
        raise ValueError(
            "Unsupported 3D model output format: "
            + output_format
        )

    loaded = trimesh.load(
        file_path,
        force="scene",
        process=False
    )

    if isinstance(loaded, trimesh.Trimesh):
        scene = trimesh.Scene(loaded)
    else:
        scene = loaded

    if not isinstance(scene, trimesh.Scene):
        raise ValueError(
            "Could not load the input as a 3D model"
        )

    if not scene.geometry:
        raise ValueError(
            "The 3D model contains no geometry"
        )

    output_path = pathlib.Path(
        output_file_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if output_format in {"stl", "ply"}:
        # STL and PLY are treated as single-mesh outputs.
        # Multiple meshes in a scene are merged into one mesh.
        meshes = [
            geometry.copy()
            for geometry in scene.geometry.values()
            if isinstance(
                geometry,
                trimesh.Trimesh
            )
        ]

        if not meshes:
            raise ValueError(
                "The 3D model contains no mesh geometry"
            )

        mesh = (
            meshes[0]
            if len(meshes) == 1
            else trimesh.util.concatenate(
                meshes
            )
        )

        mesh.export(
            str(output_path),
            file_type=output_format
        )
    else:
        # OBJ and GLB can represent a scene with multiple objects.
        scene.export(
            file_obj=str(output_path),
            file_type=output_format
        )

    if (
        not output_path.is_file()
        or output_path.stat().st_size <= 0
    ):
        raise RuntimeError(
            "3D model converter did not create "
            "a valid output file"
        )

    return str(output_path)
