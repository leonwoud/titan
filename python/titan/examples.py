from titan.vendor.maya import Maya


class Example:
    def __init__(self):
        self._callback_id = Maya.event_manager.register_callback(
            Maya.events.SelectionChanged, self.selection_changed
        )

    def selection_changed(self):
        print(Maya.cmds.ls(sl=True))

    def unregister(self):
        Maya.event_manager.remove_callback(self._callback_id)
