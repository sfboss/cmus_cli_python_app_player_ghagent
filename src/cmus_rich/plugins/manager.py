"""Plugin manager for loading and managing plugins."""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional

from cmus_rich.plugins.api import Plugin


class PluginManager:
    """Manages plugins for CMUS Rich."""

    def __init__(self, plugin_dir: str = "plugins") -> None:
        self.plugin_dir = Path(plugin_dir)
        self.plugins: dict[str, Plugin] = {}
        self.app: Optional[Any] = None

    def set_app(self, app: Any) -> None:
        """Set the application instance."""
        self.app = app

    async def load_plugins(self) -> None:
        """Load all plugins from plugin directory."""
        if not self.plugin_dir.exists():
            return

        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            await self._load_plugin(plugin_file)

    async def _load_plugin(self, plugin_file: Path) -> None:
        """Load a single plugin file."""
        try:
            # Import the plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_file.stem}", plugin_file
            )
            if not spec or not spec.loader:
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Look for Plugin class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr != Plugin
                ):
                    # Instantiate plugin
                    if self.app:
                        plugin = attr(self.app)
                        await plugin.initialize()
                        self.plugins[plugin.name] = plugin
                        print(f"Loaded plugin: {plugin.name} v{plugin.version}")
                    break

        except Exception as e:
            print(f"Failed to load plugin {plugin_file}: {e}")

    async def unload_plugins(self) -> None:
        """Unload all plugins."""
        for plugin in self.plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                print(f"Error cleaning up plugin {plugin.name}: {e}")

        self.plugins.clear()

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    async def notify_track_change(self, track: Any) -> None:
        """Notify all plugins of track change."""
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    await plugin.on_track_change(track)
                except Exception as e:
                    print(f"Error in plugin {plugin.name} on_track_change: {e}")
