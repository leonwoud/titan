import ast
import importlib
import sys
from typing import Any, Dict, Optional, List, Set, Union


def execfile(
        file_path: str,
        globals: Optional[Dict[str, Any]] = None,
        locals: Optional[Dict[str, Any]] = None
):
    """Execute the given file, replacement for python 2's execfile."""
    if globals is None:
        globals = {}
    globals.update({
        "__file__": file_path,
        "__name__": "__main__",
    })
    with open(file_path, 'rb') as file:
        exec(compile(file.read(), file_path, 'exec'), globals, locals)


def _get_module_imports(module) -> Set[str]:
    """Extract titan module imports from a module's source code."""
    if not hasattr(module, '__file__') or not module.__file__:
        return set()
    
    try:
        with open(module.__file__, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('titan'):
                        imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('titan'):
                    imports.add(node.module)
        
        return imports
    except:
        return set()


def _find_dependents(target_module_name: str) -> Set[str]:
    """Find all loaded titan modules that import the target module."""
    dependents = set()
    
    for name, module in sys.modules.items():
        if not name.startswith('titan') or name == target_module_name:
            continue
        
        imports = _get_module_imports(module)
        if target_module_name in imports:
            dependents.add(name)
    
    return dependents


def _get_reload_order(target_module_name: str) -> List[str]:
    """Get the order in which modules should be reloaded."""
    to_reload = set()
    
    def add_dependents(module_name: str):
        """Recursively add modules that depend on this module."""
        dependents = _find_dependents(module_name)
        for dependent in dependents:
            if dependent not in to_reload:
                to_reload.add(dependent)
                add_dependents(dependent)
    
    # Add the target module
    to_reload.add(target_module_name)
    
    # Add all modules that depend on the target
    add_dependents(target_module_name)
    
    # Simple ordering: dependencies first, then dependents
    # Get dependencies for each module to reload
    module_deps = {}
    for module_name in to_reload:
        if module_name in sys.modules:
            deps = _get_module_imports(sys.modules[module_name])
            # Only include deps that are also being reloaded
            module_deps[module_name] = deps.intersection(to_reload)
    
    # Topological sort
    ordered = []
    remaining = to_reload.copy()
    
    while remaining:
        # Find modules with no unresolved dependencies
        ready = []
        for module in remaining:
            deps = module_deps.get(module, set())
            if all(dep in ordered for dep in deps):
                ready.append(module)
        
        if not ready:
            # Break cycles by picking modules with fewest remaining deps
            ready = [min(remaining, key=lambda m: len(module_deps.get(m, set()) - set(ordered)))]
        
        ready.sort()
        ordered.extend(ready)
        
        for module in ready:
            remaining.remove(module)
    
    return ordered


def reload(module: Union[str, Any], verbose: bool = True) -> bool:
    """Reload a module and all its dependents in correct order.
    
    This function automatically discovers dependencies by analyzing import statements
    and reloads everything that depends on the target module.
    
    Args:
        module: The module to reload (module object or string name)
        verbose: If True, print information about what's being reloaded
        
    Returns:
        True if reload was successful, False otherwise
        
    Examples:
        >>> import titan.widgets
        >>> from titan.dbg import reload
        >>> reload(titan.widgets)  # Reloads widgets and everything that depends on it
        
        >>> from titan._internal.preferences import editor
        >>> reload(editor)  # Reloads just the editor and its dependents
    """
    try:
        # Get module name
        if isinstance(module, str):
            module_name = module
        else:
            module_name = getattr(module, '__name__', str(module))
        
        if not module_name.startswith('titan'):
            if verbose:
                print(f"Module '{module_name}' is not a titan module")
            return False
        
        # Get reload order
        reload_order = _get_reload_order(module_name)

        # Reload each module
        reloaded_count = 0
        failed_modules = []
        
        for mod_name in reload_order:
            if mod_name in sys.modules:
                try:
                    importlib.reload(sys.modules[mod_name])
                    reloaded_count += 1
                    if verbose:
                        print(f"  > Reloaded {mod_name}")
                except Exception as e:
                    failed_modules.append((mod_name, str(e)))
                    if verbose:
                        print(f"  x Failed to reload {mod_name}: {e}")
            else:
                if verbose:
                    print(f"  - Skipped {mod_name} (not loaded)")
        
        success = len(failed_modules) == 0
        
        if verbose:
            total_attempted = len([m for m in reload_order if m in sys.modules])
            print(f"\nReload complete: {reloaded_count}/{total_attempted} modules reloaded successfully")
            
            if failed_modules:
                print("Failed modules:")
                for mod_name, error in failed_modules:
                    print(f"  - {mod_name}: {error}")
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"Reload failed: {e}")
        return False
