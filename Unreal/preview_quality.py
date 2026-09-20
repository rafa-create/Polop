"""Execute in Unreal to toggle lightweight viewport / restore prior settings.

Session-only: no map saves, INI edits, sequence edits or render submissions.
Restore before configuring Movie Render Queue. Restoration is not a final preset.
"""
import sys
import types
import unreal

_STATE_KEY = "_polop_light_preview_state"
# Preserve contact shadows; reduce resolution and costly Lumen/translucency work.
_PREVIEW = {
    "r.ScreenPercentage": 60.0,
    "r.ShadowQuality": 3.0,
    "r.Shadow.MaxResolution": 1024.0,
    "r.SSR.Quality": 0.0,
    "r.Lumen.DiffuseIndirect.Allow": 0.0,
    "r.Lumen.Reflections.Allow": 0.0,
    "r.VolumetricFog": 0.0,
    "r.MotionBlurQuality": 0.0,
    "t.MaxFPS": 30.0,
}


def toggle_preview():
    system = unreal.SystemLibrary
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    state = sys.modules.get(_STATE_KEY)
    restoring = state is not None
    if state is None:
        state = types.ModuleType(_STATE_KEY)
        state.original = {name: system.get_console_variable_float_value(name)
                          for name in _PREVIEW}
        # Store before applying, so even partial failure can be restored.
        sys.modules[_STATE_KEY] = state
    requested = state.original if restoring else _PREVIEW
    failed = []
    for name, value in requested.items():
        system.execute_console_command(world, "%s %s" % (name, value))
        actual = system.get_console_variable_float_value(name)
        if abs(actual-value) > 0.01:
            failed.append(name)
    if failed:
        raise RuntimeError("Preview settings not applied: %s. Run again to restore." % failed)
    if restoring:
        del sys.modules[_STATE_KEY]
        unreal.log("POLOP: previous settings restored. Configure and verify final render separately.")
    else:
        unreal.log("POLOP: light preview enabled (session only). Run this script again to restore. "
                   "Lighting differs from final rendering; FPS is not guaranteed.")


if __name__ == "__main__":
    toggle_preview()
