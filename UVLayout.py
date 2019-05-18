from math import floor, ceil
import maya.cmds as cmds


class UI(object):
    def __init__(self):
        self.win_id = 'Layout_UVs'
        self.start_tile = None
        self.shell_spacing = None
        self.arrange_button = None

    def create_ui(self):
        if cmds.window(self.win_id, ex=1):
            cmds.deleteUI(self.win_id, window=True)

        cmds.window(self.win_id, title='Arrange & Layout UVs', width=250)
        clm_lyt = cmds.columnLayout(adjustableColumn=True)
        row_lyt = cmds.rowColumnLayout(nc=3, adj=3)
        start_tile_label = cmds.text("Start Tile", width=80)
        self.start_tile = cmds.textField(text=1, changeCommand=self._validate_entries)
        self.use_current_tile = cmds.checkBox(l="Use shell's current tile", changeCommand=self._tile_decision)

        start_tile_label = cmds.text("Shell Spacing", width=80)
        self.shell_spacing = cmds.textField(text=0.03, changeCommand=self._validate_entries)

        cmds.text(l='', h=3)

        stack_tile = cmds.text("Stack Columns", width=80)
        self.stack_columns = cmds.textField(text=3, enable=False, changeCommand=self._validate_entries)
        self.use_stacking = cmds.checkBox(l="Stack UVs", changeCommand=self._require_stacking)

        cmds.text(l='', h=3)
        cmds.text(l='', h=3)
        cmds.setParent("..")

        cmds.separator(p=clm_lyt, height=10, style='none')
        self.note_text = cmds.text(l='', p=clm_lyt, enable=False)
        self.arrange_button = cmds.button(l='Layout UVs', command=self._run_arrangement, h=30, enable=True)

        cmds.showWindow()

    def _run_arrangement(self, *args):
        selected = self._check_selection()
        if not selected:
            return
        shell_spacing = float(cmds.textField(self.shell_spacing, text=True, query=True))
        use_stacking = cmds.checkBox(self.use_stacking, v=True, query=True)
        stack_columns = int(cmds.textField(self.stack_columns, text=True, query=True))
        start_tile = int(cmds.textField(self.start_tile, text=True, query=True))
        use_current_tile = cmds.checkBox(self.use_current_tile, v=True, query=True)
        run_arrangement(start_tile, shell_spacing, use_current_tile, use_stacking, stack_columns)

    def _check_selection(self, *args):
        selection = cmds.ls(sl=True)
        if not selection:
            cmds.text(self.note_text, e=True, l='Please select objects to layout UVs for', enable=True)
            return False
        else:
            cmds.text(self.note_text, e=True, l='', enable=False)
            return True

    def _require_stacking(self, *args):
        use_stacking = cmds.checkBox(self.use_stacking, q=True, v=True)
        if use_stacking:
            cmds.textField(self.stack_columns, e=True, text=3, enable=True)
        else:
            cmds.textField(self.stack_columns, e=True, enable=False)
            cmds.text(self.note_text, e=True, l='', enable=False)
            cmds.button(self.arrange_button, e=True, enable=True)

    def _tile_decision(self, *args):
        use_current_tile = cmds.checkBox(self.use_current_tile, q=True, v=True)
        if use_current_tile:
            cmds.textField(self.start_tile, e=True, enable=False)
        else:
            cmds.textField(self.start_tile, e=True, enable=True)

    def _validate_entries(self, *args):
        start_tile = cmds.textField(self.start_tile, text=True, query=True)
        shell_spacing = cmds.textField(self.shell_spacing, text=True, query=True)
        stack_columns = cmds.textField(self.stack_columns, text=True, query=True)
        if start_tile == '' or shell_spacing == '':
            cmds.text(self.note_text, e=True, l='Please enter values for both Start Tile and Shell Spacing',
                      enable=True)
            cmds.button(self.arrange_button, e=True, enable=False)
        elif int(start_tile) == 0:
            cmds.text(self.note_text, e=True, l='Start Tile should be greater than 0', enable=True)
            cmds.button(self.arrange_button, e=True, enable=False)
        elif stack_columns == '' or int(stack_columns) == 0:
            cmds.text(self.note_text, e=True, l='Please enter a valid value(> 0) for Stack Columns', enable=True)
            cmds.button(self.arrange_button, e=True, enable=False)
        else:
            cmds.text(self.note_text, e=True, l='', enable=False)
            cmds.button(self.arrange_button, e=True, enable=True)


class Shell(object):
    def __init__(self, shell, shell_spacing=0):
        self.shell = shell
        self.shell_spacing = shell_spacing
        self.bbox_coords = cmds.polyEvaluate(self.shell, b2=True)

    @property
    def height(self):
        y1 = self.bbox_coords[1][0]
        y2 = self.bbox_coords[1][1]
        return (y2 - y1) + self.shell_spacing

    @property
    def width(self):
        x1 = self.bbox_coords[0][0]
        x2 = self.bbox_coords[0][1]
        return (x2 - x1) + self.shell_spacing

    @property
    def shell_coordinates(self):
        x = self.bbox_coords[0][0] - self.shell_spacing
        y = self.bbox_coords[1][0] - self.shell_spacing
        coord = Point(x, y)
        return coord


class Point(object):
    def __init__(self, u, v):
        self.u = u
        self.v = v

    def __add__(self, other):
        new_u = self.u + other.u
        new_v = self.v + other.v
        return Point(new_u, new_v)

    def __sub__(self, other):
        new_u = self.u - other.u
        new_v = self.v - other.v
        return Point(new_u, new_v)


class Tile(object):
    def __init__(self, shell_width, shell_height, height=1, width=1):
        self.height = height
        self.width = width
        self._next = origin
        self.shell_width = shell_width
        self.shell_height = shell_height

    def add_identical_shells(self, shells, shell_spacing):
        shells_per_row_count = 1
        for shell in shells:
            shell_obj = Shell(shell, shell_spacing)
            if shells_per_row_count <= self.shells_per_row:
                target_uv = self._next
            else:
                shells_per_row_count = 1
                target_uv = Point(origin.u, target_uv.v + shell_obj.height)
            self._next = self._move_and_get_next(target_uv, shell_obj)
            shells_per_row_count += 1

    def stack_together(self, shells, shell_spacing, columns):
        shells_per_column_count = 1
        shells_per_row_count = 1
        u_next = origin.u
        for shell in shells:
            shell_obj = Shell(shell, shell_spacing)
            if shells_per_row_count <= columns:
                target_uv = self._next
            else:
                shells_per_column_count += 1
                shells_per_row_count = 1
                target_uv = Point(u_next, target_uv.v + shell_obj.height)
                if shells_per_column_count > self.shells_per_column:
                    target_uv = Point(self.shell_width * columns, origin.v)
                    u_next = target_uv.u
                    shells_per_column_count = 1

            self._next = self._move_and_get_next(target_uv, shell_obj)
            shells_per_row_count += 1

    def _move_and_get_next(self, target_uv, shell_obj):
        move_uv = target_uv - shell_obj.shell_coordinates
        self._move_shell(shell_obj.shell, move_uv)
        next_position = target_uv + Point(shell_obj.width, 0)
        return next_position

    @property
    def shells_per_column(self):
        return floor(self.height / self.shell_height)

    @property
    def shells_per_row(self):
        return floor(self.width / self.shell_width)

    @staticmethod
    def _move_shell(shell, move_uv):
        cmds.select(cmds.polyListComponentConversion(shell, tuv=True))
        cmds.polyEditUV(u=move_uv.u, v=move_uv.v)
        cmds.select(clear=True)


class Origin(object):
    @staticmethod
    def get_next_tile_origin():
        current_origin = origin
        if current_origin.u == 9:
            current_origin.u = 0
            current_origin.v += 1
        else:
            current_origin.u += 1
        next_origin = Point(current_origin.u, current_origin.v)
        return next_origin

    @staticmethod
    def get_start_tile_origin(start_tile):
        if start_tile <= 10:
            u = start_tile - 1
            v = 0
        else:
            u = (start_tile % 10) - 1
            v = (start_tile // 10)
            if u < 0:
                u = 9
                v -= 1
        start_origin = Point(u, v)
        return start_origin

    @staticmethod
    def get_shells_current_tile_origin(shell):
        shell = Shell(shell)
        coord = shell.shell_coordinates
        start_origin = Point(int(floor(coord.u)), int(floor(coord.v)))
        return start_origin


def tile_requirement_per_topology(topology, shells, shell_spacing, shells_per_tile):
    tile_info = {}
    shell = Shell(shells[0], shell_spacing)
    total_shells = len(shells)
    tile_count = int(ceil((1.0 / shells_per_tile) * total_shells))
    tile_info[topology] = {'tile_count': tile_count,
                           'shells_per_tile': shells_per_tile,
                           'all_shells': shells,
                           'shell_width': shell.width,
                           'shell_height': shell.height}
    return tile_info


def arrange_shells_for_topology(topology, shell_spacing, use_stacking, stack_columns):
    global origin
    tilewise_shell_count = segregate_available_shells_into_tiles(topology['shells_per_tile'],
                                                                 topology['all_shells'])
    for tile_number in range(topology['tile_count']):
        tile = Tile(topology['shell_width'], topology['shell_height'])
        if use_stacking:
            tile.stack_together(tilewise_shell_count[tile_number], shell_spacing, stack_columns)
        else:
            tile.add_identical_shells(tilewise_shell_count[tile_number], shell_spacing)
        origin = Origin.get_next_tile_origin()


def segregate_available_shells_into_tiles(shells_per_tile, all_shells):
    tilewise_shell_count = {}
    for tile, shell in enumerate(range(0, len(all_shells), shells_per_tile), 0):
        tilewise_shell_count[tile] = all_shells[shell:shell + shells_per_tile]
    return tilewise_shell_count


def get_origin(start_tile, use_current_tile, shell):
    if use_current_tile:
        start_origin = Origin.get_shells_current_tile_origin(shell)
    else:
        start_origin = Origin.get_start_tile_origin(start_tile)
    return start_origin


def get_shells_per_tile(topology_shell, shell_spacing, tile_height=1.0, tile_width=1.0):
    shell = Shell(topology_shell, shell_spacing)
    shells_per_row = floor(tile_width / shell.width)
    shells_per_column = floor(tile_height / shell.height)
    shells_per_tile = shells_per_row * shells_per_column
    return floor(shells_per_tile)


def group_objects_on_topology(selected_objects):
    topologies = {}
    for object in selected_objects:
        vertex = cmds.polyEvaluate(object, vertex=True)
        edge = cmds.polyEvaluate(object, edge=True)
        face = cmds.polyEvaluate(object, face=True)
        uvshells = cmds.polyEvaluate(object, uvShell=True)
        uvarea = round(cmds.polyEvaluate(object, uvArea=True), 3)
        key = '%s_%s_%s_%s' % (vertex, edge, face, uvshells)
        final_key = key_with_uvarea(topologies, uvarea, key)
        if final_key in topologies:
            topologies[final_key].append(object)
        else:
            topologies[final_key] = [object]
    return topologies


def key_with_uvarea(topologies, uvarea, key):
    if topologies:
        uvarea = get_matching_uvarea(topologies, uvarea, key)
    final_key = '%s_%s' % (key, uvarea)
    return final_key


def get_matching_uvarea(topologies, uvarea, key):
    for topology_key in topologies:
        if key in topology_key:
            topology_key_area = float(topology_key.split('_')[-1])
            uvarea = check_for_area_within_tolerance(uvarea, topology_key_area)
    return uvarea


def check_for_area_within_tolerance(uvarea, topology_key_area):
    tolerance_limit = (1 - uvarea / topology_key_area) * 100
    if abs(tolerance_limit) <= 5:
        uvarea = topology_key_area
    return uvarea


def run_arrangement(start_tile, shell_spacing, use_current_tile, use_stacking, stack_columns, *args):
    global origin
    unarranged = set()
    selection = cmds.ls(sl=True)
    selected_objects, parent_dict = get_selection_list_children(selection)
    topology_groups = group_objects_on_topology(selected_objects)
    origin = get_origin(start_tile, use_current_tile, selected_objects[0])

    for topology in topology_groups:
        shells = topology_groups[topology]
        shells_per_tile = int(get_shells_per_tile(shells[0], shell_spacing))
        if shells_per_tile:
            tile_info = tile_requirement_per_topology(topology, shells, shell_spacing, shells_per_tile)
            arrange_shells_for_topology(tile_info[topology], shell_spacing, use_stacking, stack_columns)
        else:
            for shell in shells:
                unarranged.add(parent_dict[str(shell)])
    if unarranged:
        notify_unarranged_nodes(unarranged)
    cmds.select(selection)


def notify_unarranged_nodes(unarranged):
    message = 'Following groups/meshes could not be arranged.\n' \
              'Please arrange manually.\n\n\t{}'.format(('\n\t'.join(unarranged)))
    cmds.confirmDialog(title="Unarranged UVs", message=message, button="OK")


def get_selection_list_children(selection):
    selection_list_children = []
    parent_child_dict = {}
    for node in selection:
        node_children = cmds.listRelatives(node, c=True)
        parent_child_dict[str(node_children)] = node
        selection_list_children.append(node_children)
    return selection_list_children, parent_child_dict


def main():
    ui = UI()
    ui.create_ui()


if __name__ == '__main__':
    ui = UI()
    ui.create_ui()
