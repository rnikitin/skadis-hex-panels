"""Studio renders of the released STL geometry: front, joined tiles and rear ribs.

Requires VTK and NumPy. No geometry is changed for rendering.
"""

from pathlib import Path
import argparse
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/images"
PANEL = ROOT / "PRINT_THIS/S01_panel.stl"
NEIGHBOURS = [
    (0, 0),
    (180, 100),
    (0, 200),
    (-180, 100),
    (-180, -100),
    (0, -200),
    (180, -100),
]


def load_mesh(file):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(file))
    reader.Update()
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(reader.GetOutputPort())
    normals.SetFeatureAngle(35)
    normals.SplittingOn()
    normals.ConsistencyOn()
    normals.AutoOrientNormalsOn()
    normals.Update()
    return normals.GetOutput()


def environment():
    h, w = 128, 256
    y, x = np.mgrid[0:h, 0:w]
    value = 0.16 + 0.34 * np.sin(np.pi * (y + 0.5) / h)
    value += 2.0 * np.exp(
        -(((x - w * 0.18) / (w * 0.07)) ** 8) - ((y - h * 0.28) / (h * 0.16)) ** 8
    )
    value += 1.1 * np.exp(
        -(((x - w * 0.72) / (w * 0.12)) ** 8) - ((y - h * 0.35) / (h * 0.2)) ** 8
    )
    pixels = np.stack([value * 1.01, value, value * 0.98], axis=-1).astype(np.float32)
    data = vtk.vtkImageData()
    data.SetDimensions(w, h, 1)
    scalars = numpy_to_vtk(pixels.reshape(-1, 3), deep=True)
    scalars.SetName("studio")
    data.GetPointData().SetScalars(scalars)
    texture = vtk.vtkTexture()
    texture.SetInputData(data)
    texture.InterpolateOn()
    texture.MipmapOn()
    return texture


def actor(mesh, position=(0, 0, 0), color=(0.87, 0.87, 0.855), roughness=0.7):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(mesh)
    a = vtk.vtkActor()
    a.SetMapper(mapper)
    a.SetPosition(*position)
    p = a.GetProperty()
    p.SetInterpolationToPBR()
    p.SetColor(*color)
    p.SetMetallic(0)
    p.SetRoughness(roughness)
    return a


def render(file, mesh, centres, camera_direction, wall_z, size=(2200, 1800)):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.80, 0.815, 0.825)
    renderer.SetUseImageBasedLighting(True)
    renderer.SetEnvironmentTexture(environment())
    renderer.AutomaticLightCreationOff()
    renderer.SetUseFXAA(True)
    b = mesh.GetBounds()
    cx = (b[0] + b[1]) / 2
    cy = (b[2] + b[3]) / 2
    minx = min(x + b[0] - cx for x, y in centres)
    maxx = max(x + b[1] - cx for x, y in centres)
    miny = min(y + b[2] - cy for x, y in centres)
    maxy = max(y + b[3] - cy for x, y in centres)
    mx, my = (minx + maxx) / 2, (miny + maxy) / 2
    span = max(maxx - minx, maxy - miny)
    for x, y in centres:
        renderer.AddActor(actor(mesh, (x - cx, y - cy, 0)))
    # The neutral studio plane is behind the front-view panels, or below
    # the face-down panel for the rear product view.
    plane = vtk.vtkPlaneSource()
    extent = span * 3
    plane.SetOrigin(mx - extent, my - extent, wall_z)
    plane.SetPoint1(mx + extent, my - extent, wall_z)
    plane.SetPoint2(mx - extent, my + extent, wall_z)
    plane.Update()
    floor = actor(plane.GetOutput(), color=(0.72, 0.74, 0.755), roughness=1)
    renderer.AddActor(floor)
    front = camera_direction[2] < 0
    sign = -1 if front else 1
    for pos, intensity, color in [
        ((-1.1, 1.3, sign * 1.8), 1.05, (1, 0.97, 0.93)),
        ((1.2, 0.2, sign * 1.0), 0.38, (0.91, 0.95, 1)),
        ((0.2, -1.4, sign * 1.4), 0.5, (1, 1, 1)),
    ]:
        light = vtk.vtkLight()
        light.SetLightTypeToSceneLight()
        light.SetPosition(mx + pos[0] * span, my + pos[1] * span, pos[2] * span)
        light.SetFocalPoint(mx, my, 5)
        light.SetIntensity(intensity)
        light.SetColor(*color)
        renderer.AddLight(light)
    steps = vtk.vtkRenderStepsPass()
    ao = vtk.vtkSSAOPass()
    ao.SetDelegatePass(steps)
    ao.SetRadius(14)
    ao.SetBias(0.35)
    ao.SetKernelSize(128)
    ao.SetBlur(True)
    renderer.SetPass(ao)
    cam = renderer.GetActiveCamera()
    cam.SetFocalPoint(mx, my, 7)
    direction = np.asarray(camera_direction, float)
    direction /= np.linalg.norm(direction)
    cam.SetPosition(
        mx + direction[0] * span * 3,
        my + direction[1] * span * 3,
        7 + direction[2] * span * 3,
    )
    cam.SetViewUp(0, 1, 0)
    cam.ParallelProjectionOn()
    renderer.ResetCamera(minx, maxx, miny, maxy, b[4], b[5])
    cam.Zoom(1.15)
    renderer.ResetCameraClippingRange()
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetMultiSamples(0)
    window.AddRenderer(renderer)
    window.SetSize(*size)
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.SetInputBufferTypeToRGB()
    capture.ReadFrontBufferOff()
    capture.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(OUTPUT / file))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    window.Finalize()
    print(OUTPUT / file)


def main():
    global OUTPUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    if args.preview:
        OUTPUT = ROOT / "work/render-preview"
    OUTPUT.mkdir(exist_ok=True, parents=True)
    mesh = load_mesh(PANEL)
    size = (1200, 1000) if args.preview else (2400, 2000)
    render("S01_front.png", mesh, [(0, 0)], (0, 0, -1), 24, size)
    render("S01_front_assembly.png", mesh, NEIGHBOURS, (0, 0, -1), 24, size)
    render("S01_rear_oblique.png", mesh, [(0, 0)], (0.52, -0.27, 0.81), -0.3, size)
    mounts = load_mesh(ROOT / "PRINT_THIS/S01_wall_mount_2p2.stl")
    mount_centres = [(x, y) for y in (-32, 32) for x in (-66, -22, 22, 66)]
    render("S01_mounts.png", mounts, mount_centres, (0.48, -0.3, 0.83), -0.3, size)
    jig = load_mesh(ROOT / "PRINT_THIS/S01_alignment_jig_5p2.stl")
    render("S01_jig.png", jig, [(0, 0)], (0.48, -0.3, 0.83), -0.3, size)


if __name__ == "__main__":
    main()
