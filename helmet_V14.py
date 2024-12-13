    # helmet_V14.py - Blender script to make a prosthetic helmet for skull injuries
    # Copyright (C) 2024  Anonymously donated to Robert L. Read

    # This program is free software: you can redistribute it and/or modify
    # it under the terms of the GNU Affero General Public License as
    # published by the Free Software Foundation, either version 3 of the
    # License, or (at your option) any later version.

    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU Affero General Public License for more details.

    # You should have received a copy of the GNU Affero General Public License
    # along with this program.  If not, see <https://www.gnu.org/licenses/>.

import bpy
import math
import os
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import StringProperty
from mathutils import Vector,Matrix
import bmesh
import bpy.types
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, BoolProperty, PointerProperty, StringProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
import mathutils

bl_info = {
    "name": "Helmet Pipeline",
    "author": "z.e.g.",
    "version": (1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Toolbar > Object Adder",
    "description": "Adds objects and other functions to help our workflow (Tutorial Result)",
    "category": "Add Mesh",
}

class MAIN_PT_Panel(Panel):
    bl_label = "Helmet Pipeline"
    bl_idname = "MAIN_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Helmet'
    bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        pass


class JIC_PT_Panel(Panel):
    bl_label = "Just in Case:"
    bl_idname = "JIC_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_parent_id = 'MAIN_PT_Panel'
    bl_region_type = 'UI'
    bl_category = 'Helmet'
    bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout
        row=layout.row()
        row.operator('helmet.decimate_object', text='Decimate')
        row.prop(context.scene, 'decimate_factor',text="Decimate Factor")
        row.operator('helmet.apply_modifiers', text='Apply')
        row=layout.row()
        row.operator('helmet.show_head')
        row.operator('helmet.hide_head')


class ExportSTLOperator(bpy.types.Operator, ExportHelper):
    """Export as STL"""
    bl_idname = "helmet.export_stl"
    bl_label = "Export STL"

    # ExportHelper mixin class uses this
    filename_ext = ".stl"

    filter_glob: StringProperty(
        default="*.stl",
        options={'HIDDEN'},
        maxlen=255,
    )

    # STL export options
    use_ascii: BoolProperty(
        name="ASCII",
        description="Save the file in ASCII format",
        default=False,
    )

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=True,
    )

    global_scale: FloatProperty(
        name="Scale",
        description="Scale all data",
        min=0.01, max=1000.0,
        default=1.0,
    )

    def execute(self, context):
        # Call the STL export function
        for obj in bpy.data.objects:
            if("helmet" in obj.name and "backup" not in obj.name ) or "holder" == obj.name:
                obj.select_set(True)
        return bpy.ops.export_mesh.stl(
            filepath=self.filepath,
            use_selection=self.use_selection,
            ascii=self.use_ascii,
            global_scale=self.global_scale,
        )

class Decimate_Object_Operator(Operator):
    bl_idname = "helmet.decimate_object"
    bl_label = "Decimate Object"

    def execute(self, context):
        obj = bpy.data.objects.get("helmet")


        if obj is None or obj.type != 'MESH':
            print("No active mesh object selected.")
            return

        # Check for existing decimate modifier
        decimate_mod = next((mod for mod in obj.modifiers if mod.type == 'DECIMATE'), None)

        # Update existing modifier or add a new one
        if decimate_mod:
            decimate_mod.ratio = context.scene.decimate_factor
        else:
            decimate_mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
            decimate_mod.ratio = context.scene.decimate_factor

        return {'FINISHED'}

class Show_Backup_Operator(Operator):
    bl_idname = "helmet.show_backup"
    bl_label = "Show Head"

    def execute(self, context):
        obj = bpy.data.objects.get("helmet_backup")
        if obj is None or obj.type != 'MESH':
            obj.hide_viewport=False

        return {'FINISHED'}

class Show_Head_Operator(Operator):
    bl_idname = "helmet.show_head"
    bl_label = "Show Head"

    def execute(self, context):
        obj = bpy.data.objects.get("helmet_backup")
        if(obj):
            obj.hide_viewport = False
        return {'FINISHED'}


class Hide_Head_Operator(Operator):
    bl_idname = "helmet.hide_head"
    bl_label = "Hide Head"

    def execute(self, context):
        obj = bpy.data.objects.get("helmet_backup")
        if(obj):
            obj.hide_viewport = True
        return {'FINISHED'}


class Hinge_Add_Operator(Operator):
    bl_idname = "helmet.add_hinge"
    bl_label = "Add Hinge"

    def execute(self, context):
        for obj in bpy.data.objects:
            if obj.name == "hinge":
                bpy.data.objects.remove(obj)

        # Find the helmet object and add a boolean modifier with the cutter
        helmet = bpy.data.objects.get("helmet")
        if helmet:
            cutter = append_and_rename_object(os.path.join(os.path.dirname(__file__),"assets.blend"), 'hinge', 'hinge')

            #make_wireframe(cutter)
            cutter.name = "hinge"

            cutter.location = average_position_of_top_face(helmet)
            cutter.location[2]+=10
            #cutter.rotation_euler = (0,math.radians(90), 0)
            bpy.context.view_layer.update()

            self.assign_properties()
            #self.add_boolean_modifier("helmet", "hinge","BooleanMod_add_hinge")

            """
            boolean_modifier = helmet.modifiers.new(name="BooleanMod_cut_ear", type='BOOLEAN')
            boolean_modifier.solver="FAST"
            bpy.context.view_layer.update()

            boolean_modifier.object = cutter
            boolean_modifier.operation = 'DIFFERENCE'
            """

        else:
            print("Helmet object not found")
        return {'FINISHED'}

    def add_boolean_modifier(self,target_object, operand_object_name,mod_name):
        # Ensure the target object exists
        if target_object not in bpy.data.objects:
            print(f"Object {target_object} not found")
            return

        # Ensure the operand object exists
        if operand_object_name not in bpy.data.objects:
            print(f"Operand object {operand_object_name} not found")
            return

        obj = bpy.data.objects[target_object]
        operand_obj = bpy.data.objects[operand_object_name]

        # Add a Boolean modifier with properties from the image
        bool_modifier = obj.modifiers.new(name=mod_name, type='BOOLEAN')

        bool_modifier.operation = 'UNION'
        bool_modifier.object = operand_obj
        bool_modifier.solver = 'EXACT'
        bool_modifier.use_self = True
        bool_modifier.show_viewport=False
        # Not visible in the image, but assuming default values for other properties
        # Uncomment and adjust as necessary
        # bool_modifier.double_threshold = 0
        # bool_modifier.use_hole_tolerant = False

        print(f"Boolean modifier added to {target_object} with {operand_object_name} as operand.")

    def refresh_scene_props(self):

        bpy.context.scene.hinge_size_x += 1
        bpy.context.scene.hinge_size_x -= 1

        bpy.context.scene.hinge_size_y += 1
        bpy.context.scene.hinge_size_y -= 1

        bpy.context.scene.hinge_height += 1
        bpy.context.scene.hinge_height -= 1

        bpy.context.scene.hinge_resolution_x += 1
        bpy.context.scene.hinge_resolution_x -= 1

        bpy.context.scene.hinge_resolution_y += 1
        bpy.context.scene.hinge_resolution_y -= 1

        bpy.context.scene.hinge_bottom_scale += 1
        bpy.context.scene.hinge_bottom_scale -= 1

        bpy.context.scene.hinge_edge_offset += 1
        bpy.context.scene.hinge_edge_offset -= 1

        bpy.context.scene.hinge_hole_dept += 1
        bpy.context.scene.hinge_hole_dept -= 1

        bpy.context.scene.hinge_holder_obj_marigin += 1
        bpy.context.scene.hinge_holder_obj_marigin -= 1

        bpy.context.scene.hinge_bottom_bury_offset += 1
        bpy.context.scene.hinge_bottom_bury_offset -= 1

        bpy.context.scene.hinge_diameter += 1
        bpy.context.scene.hinge_diameter -= 1


    def add_driver(self,obj,prop_name,index):
        driver = obj.modifiers['GeometryNodes'].driver_add('["Input_'+str(index)+'"]').driver
        if("var" not in [var.name for var in driver.variables]):
            var = driver.variables.new()
        else:
            var=driver.variables["var"]
        driver.expression="var"
        var.type = 'CONTEXT_PROP'
        var.name = "var"

        var.targets[0].data_path = '["'+prop_name+'"]'


    def assign_properties(self):#hinge_diameter added

        self.refresh_scene_props()

        # replace 'ObjectName' with the name of your object
        obj = bpy.data.objects['hinge']
        bpy.context.view_layer.objects.active = obj  # Set the object as the active object


        driver = obj.modifiers['GeometryNodes'].driver_add('["Input_2"]').driver
        if("var" not in [var.name for var in driver.variables]):
            var = driver.variables.new()
        else:
            var=driver.variables["var"]
       #didnt do this for others zeg
        driver.expression="var"
        driver.expression += " "
        driver.expression = driver.expression[:-1]
        var.type = 'CONTEXT_PROP'
        var.name = "var"
        var.targets[0].data_path = '["hinge_size_x"]'



        driver = obj.modifiers['GeometryNodes'].driver_add('["Input_3"]').driver
        if("var" not in [var.name for var in driver.variables]):
            var = driver.variables.new()
        else:
            var=driver.variables["var"]
        driver.expression="var"
        var.type = 'CONTEXT_PROP'
        var.name = "var"

        var.targets[0].data_path = '["hinge_size_y"]'



        self.add_driver(obj,"hinge_height",4)
        self.add_driver(obj,"hinge_resolution_x",5)
        self.add_driver(obj,"hinge_bottom_bury_offset",6)
        self.add_driver(obj,"hinge_resolution_x",12)
        self.add_driver(obj,"hinge_resolution_y",6)
        self.add_driver(obj,"hinge_bottom_scale",5)
        self.add_driver(obj,"hinge_edge_offset",7)
        self.add_driver(obj,"hinge_hole_dept",8)
        self.add_driver(obj,"hinge_holder_obj_marigin",9)
        self.add_driver(obj,"hinge_bottom_bury_offset",11)
        self.add_driver(obj,"hinge_diameter",13)



        #.modifiers['GeometryNodes']["Input_10"]=bpy.data.objects["helmet"]
        obj.modifiers["GeometryNodes"]["Input_10"] = bpy.data.objects["helmet"]

class STEP1_PT_Panel(Panel):
    bl_label = "Step 1: Setup"
    bl_idname = "STEP1_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_parent_id = 'MAIN_PT_Panel'
    bl_region_type = 'UI'
    bl_category = 'Helmet'
    bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout
        row=layout.row()
        row.operator('helmet.solidify_object', text='Add Thickness')
        row.prop(context.scene, 'solidify_thickness',text="thickness value")
        row.operator('helmet.apply_modifiers', text='Apply')
        row=layout.row()
        row.operator('helmet.cut_bottom_half', text = 'Add Bottom Cutter')
        row.operator('helmet.apply_modifiers', text='Apply')
        row=layout.row()
        row.operator('helmet.cut_ear', text='Add Ear Cutter')
        row.operator('helmet.apply_modifiers', text='Apply')
        row=layout.row()
        row.operator('helmet.cut_face', text='Add Face Cutter')
        row.operator('helmet.apply_modifiers', text='Apply')

class STEP2_PT_Panel(Panel):
    bl_label = "Step 2: Detailing"
    bl_idname = "STEP2_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Helmet'
    bl_parent_id = 'MAIN_PT_Panel'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order=2

    def draw(self, context):
        layout = self.layout
        row=layout.row()
        row.operator('helmet.add_hinge', text='Add Hinge')
        row=layout.row()
        row.prop(context.scene, 'hinge_size_x',text="X")
        row.prop(context.scene, 'hinge_size_y',text="Y")
        for prop in ["hinge_height","hinge_resolution_x","hinge_resolution_y","hinge_bottom_scale","hinge_edge_offset","hinge_hole_dept","hinge_holder_obj_marigin","hinge_bottom_bury_offset"]:
            row=layout.row()
            row.prop(context.scene, prop)#,text=prop.name add later zeg

        row=layout.row()
        row.prop(context.scene, 'hinge_diameter',text="Diameter:")
        row=layout.row()
        row.operator('helmet.apply_modifiers', text='Apply')


class STEP3_PT_Panel(Panel):
    bl_label = "Step 3: Advancement"
    bl_idname = "STEP3_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Helmet'
    bl_parent_id = 'MAIN_PT_Panel'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order=3

    def draw(self, context):
        layout = self.layout

        row=layout.row()
        row.operator("helmet.cut_mid", text="Cut Middle")
        row.operator("helmet.apply_modifiers", text="Apply")

        row=layout.row()
        row.operator("helmet.add_supports",text="Add Left Support")
        row.operator("helmet.apply_modifiers", text="Apply")
        row=layout.row()
        row.operator("helmet.add_supports",text="Add Right Support")
        row.operator("helmet.apply_modifiers", text="Apply")

        row=layout.row()
        row.prop(context.scene, 'support_length',text="length")
        row.prop(context.scene, 'support_diameter',text="diameter")

        #row.operator("helmet.show_head")
        row=layout.row()
        row.operator("helmet.export_stl")

class Set_Unit_Scale_Operator(Operator):
    bl_idname = "helmet.set_unit_scale"
    bl_label = "Set Unit Scale"

    def execute(self, context):
        bpy.context.scene.unit_settings.scale_length = 0.001
        bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
        bpy.context.space_data.overlay.grid_scale = 0.001
        return {'FINISHED'}

class import_stl(Operator, ImportHelper):
    """Import an STL file and rename it to 'helmet'"""
    bl_idname = "helmet.import_stl"
    bl_label = "Import STL and Rename"
    filename_ext = ".stl"

    filter_glob: StringProperty(
        default="*.stl",
        options={'HIDDEN'},
        maxlen=255,
    )
    def execute(self, context):
        # Delete existing objects named 'helmet'
        for obj in bpy.data.objects:
            if obj.name == 'helmet':
                bpy.data.objects.remove(obj, do_unlink=True)

        # Import STL file
        bpy.ops.import_mesh.stl(filepath=self.filepath)

        # Rename the imported object to 'helmet'
        # Assuming the imported object is the active object
        imported_object = bpy.context.selected_objects[0]
        imported_object.name = 'helmet'
        return {'FINISHED'}

class SolidifyObjectOperator(Operator):
    bl_idname = "helmet.solidify_object"
    bl_label = "Solidify Object"

    def execute(self, context):
        obj = bpy.data.objects.get("helmet")

        if obj:

            #backup head
            create_backup_object(obj)
            bpy.context.view_layer.objects.active = obj
            # Find an existing Solidify modifier
            solidify_mod = next((mod for mod in obj.modifiers if mod.type == 'SOLIDIFY'), None)

            if solidify_mod:
                # If a Solidify modifier exists, only update its thickness
                solidify_mod.thickness = context.scene.solidify_thickness
                solidify_mod.offset = 1

            else:
                # If no Solidify modifier exists, add one and set its thickness
                solidify_mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
                solidify_mod.thickness = context.scene.solidify_thickness
                solidify_mod.offset = 1
        else:
            raise LookupError("No Helmet Found")
        return {'FINISHED'}

def create_backup_object(obj):
    # Check if the backup object already exists
    backup_obj_name = obj.name + "_backup"
    backup_obj = bpy.data.objects.get(backup_obj_name)

    # If a backup already exists, delete it
    if backup_obj:
        bpy.data.objects.remove(backup_obj, do_unlink=True)

    # Duplicate the original object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'})
    duplicated_obj = bpy.context.selected_objects[0]

    # Rename and hide the duplicated object
    duplicated_obj.name = backup_obj_name
    #duplicated_obj.hide_set(True)
    duplicated_obj.hide_viewport = True

    return duplicated_obj

class ApplyModifiersOperator(Operator):
    bl_idname = "helmet.apply_modifiers"
    bl_label = "Apply"

    def execute(self, context):
        if(bpy.context.space_data.shading.type == 'WIREFRAME'):
            bpy.context.space_data.shading.type = 'SOLID'


        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.region_3d.view_perspective = 'PERSP'

        #if a hinge is exists: add boolean to it
        for obj in bpy.data.objects:
            if("hinge" == obj.name):
                Hinge_Add_Operator.add_boolean_modifier(self,"helmet", "hinge","BooleanMod_add_hinge")


        for obj in bpy.data.objects:
            if "helmet" in obj.name and "backup" not in obj.name:
                bpy.context.view_layer.objects.active = None
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

                bpy.ops.object.transform_apply(scale=True)

                type="" #type of modifier 0 1 2
                for mod in obj.modifiers:
                    if("BooleanMod" in mod.name):
                        mod.solver = 'EXACT'
                        mod.use_self = True
                        if("hinge" in mod.name):
                            type="hinge"
                        elif("mid" in mod.name):
                            type="mid"
                    try:
                        self.apply_modifier(obj,mod.name)
                    except:
                        obj.modifiers.remove(mod)
                        print("here is a disabled or broken modifier in stack")
                if(type=="mid"):
                    self.separate_and_rename_helmet_parts(obj.name,hinge=False)
                elif(type=="hinge"):
                    self.separate_and_rename_helmet_parts(obj.name,hinge=True)


        for obj in bpy.data.objects:
            if "cutter" in obj.name or "hinge" in obj.name:
                bpy.data.objects.remove(obj)
        return {'FINISHED'}
    def apply_modifier(self,obj, modifier_name):

        bpy.context.view_layer.objects.active = obj  # Set the object as the active object
        bpy.ops.object.mode_set(mode='OBJECT')  # Ensure the object is in object mode

        if modifier_name in obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier_name)

    def separate_and_rename_helmet_parts(self,obj_name,hinge=False):
        # Ensure the object exists and is a mesh
        if obj_name not in bpy.data.objects:
            print(f"Object '{obj_name}' not found")
            return
        obj = bpy.data.objects[obj_name]
        if obj.type != 'MESH':
            print(f"Object '{obj_name}' is not a mesh")
            return

        # Select and activate the object
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.update()

        # Switch to edit mode and separate by loose parts
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.update()

        # Rename and set origin to geometry
        separated_objects = [o for o in bpy.context.selected_objects]

        for part in separated_objects:
            bpy.context.view_layer.objects.active = part
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

        if len(separated_objects) < 2:
            print(f"Not enough parts to rename in '{obj_name}'")
            return

        if(hinge):
            separated_objects.sort(key=lambda o: o.location.z, reverse=False)
            separated_objects[0].name = 'helmet'
            separated_objects[1].name = 'holder'
        else:#mid cut
            separated_objects.sort(key=lambda o: o.location.y, reverse=False)
            separated_objects[0].name = 'helmet_front'
            separated_objects[1].name = 'helmet_back'




class CutEarOperator(Operator):
    bl_idname = "helmet.cut_ear"
    bl_label = "Cut Ear"

    def execute(self, context):
        # Delete existing cutter objects
        for obj in bpy.data.objects:
            if obj.name == "cutter":
                bpy.data.objects.remove(obj)



        # Find the helmet object and add a boolean modifier with the cutter
        helmet = bpy.data.objects.get("helmet")
        if helmet:
             # Add a cylinder named 'cutter' with 90,0,0 rotation
            #bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=2, enter_editmode=False, align='WORLD', location=get_bounding_box_center_blender(helmet))
            cutter = append_and_rename_object(os.path.join(os.path.dirname(__file__),"assets.blend"), 'cutter_ear', 'cutter')

            make_wireframe(cutter)
            cutter.name = "cutter"

            cutter.location = average_position_of_bottom_face(helmet)
            scale_to_bounding_box(cutter,helmet)
            mult=0.35
            cutter.scale[1]*=mult
            cutter.scale[2]=cutter.scale[1]
            cutter.scale[0]*=2
            #cutter.rotation_euler = (0,math.radians(90), 0)
            bpy.context.view_layer.update()

            boolean_modifier = helmet.modifiers.new(name="BooleanMod_cut_ear", type='BOOLEAN')
            boolean_modifier.solver="FAST"
            bpy.context.view_layer.update()

            boolean_modifier.object = cutter
            boolean_modifier.operation = 'DIFFERENCE'
        else:
            print("Helmet object not found")
        return {'FINISHED'}

def get_bounding_box_center_blender(obj):
    local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    global_bbox_center = obj.matrix_world @ local_bbox_center
    return global_bbox_center

class CutBottomHalfOperator(Operator):
    bl_idname = "helmet.cut_bottom_half"
    bl_label = "Bottom Half Cut"

    def execute(self, context):

        # Delete existing cutter objects
        for obj in bpy.data.objects:
            if obj.name == "cutter":
                bpy.data.objects.remove(obj)
        helmet = bpy.data.objects.get("helmet")
        # Calculate the bounding box
        if ( helmet):
            bbox_obj = self.create_bounding_box(helmet)
            location = average_position_of_bottom_face(helmet)
            bpy.context.view_layer.update()
            make_wireframe(bbox_obj)
            bbox_obj.scale[0]*=1.1
            bbox_obj.scale[1]*=1.1

            self.offset_object_z_half(bbox_obj)
            #bpy.context.view_layer.objects.active=bbox_obj
            #bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            self.set_origin_to_geometry_center(bbox_obj)


            # Add boolean modifier to the original object
            boolean_mod = helmet.modifiers.new(name="BooleanMod_cut_bottom", type='BOOLEAN')
            boolean_mod.operation = 'DIFFERENCE'
            boolean_mod.solver = 'FAST'
            boolean_mod.object = bbox_obj

            # Optionally, hide the bounding box object
            return {'FINISHED'}

    def set_origin_to_geometry_center(self,obj):
        # Ensure the input is a valid Blender object
        if not isinstance(obj, bpy.types.Object):
            print("Invalid input: The input is not a Blender Object.")
            return

        # Ensure we're in object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Calculate the geometric center
        local_verts = [v.co for v in obj.data.vertices]
        geom_center = sum(local_verts, Vector()) / len(local_verts)

        # Move the object such that the geometry center goes to the origin
        obj.data.transform(Matrix.Translation(-geom_center))

        # Update the mesh with new transformation
        obj.data.update()

        # Move the object back to its original location
        obj.location += geom_center
    def offset_object_z_half(self,obj):
    # Retrieve the object by name

        # Check if the object exists
        if obj is None:
            print(f"Object '{obj.name}' not found.")
            return

        # Make sure the object's current transformations are applied
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # Calculate the Z dimension of the object
        z_dim = obj.dimensions.z

        # Offset the object by negative half of its Z dimension
        obj.location.z -= z_dim / 2
    def create_bounding_box(self,obj):
        mesh = obj.data

        # Create a BMesh from the mesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.transform(obj.matrix_world)

        # Calculate the bounds
        verts = [v.co for v in bm.verts]
        min_co = Vector(map(min, zip(*verts)))
        max_co = Vector(map(max, zip(*verts)))

        # Create the bounding box corners
        bbox_corners = [Vector(corner) for corner in [
            (min_co.x, min_co.y, min_co.z), (max_co.x, min_co.y, min_co.z),
            (max_co.x, max_co.y, min_co.z), (min_co.x, max_co.y, min_co.z),
            (min_co.x, min_co.y, max_co.z), (max_co.x, min_co.y, max_co.z),
            (max_co.x, max_co.y, max_co.z), (min_co.x, max_co.y, max_co.z)
        ]]

        # Clean up the original BMesh
        bm.free()

        # Create a new mesh for the bounding box
        bbox_mesh = bpy.data.meshes.new("cutter")
        bbox_obj = bpy.data.objects.new("cutter", bbox_mesh)

        # Link the bounding box object to the scene
        bpy.context.collection.objects.link(bbox_obj)

        # Create a new BMesh for the bounding box
        bbox_bm = bmesh.new()
        for v in bbox_corners:
            bbox_bm.verts.new(v)
        bbox_bm.verts.ensure_lookup_table()

        # Create faces
        faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
                (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        for face_verts in faces:
            bbox_bm.faces.new([bbox_bm.verts[i] for i in face_verts])

        # Update the mesh with the new data
        bbox_bm.to_mesh(bbox_mesh)
        bbox_bm.free()

        return bbox_obj

def average_position_of_bottom_face(obj):
    # Assuming obj.bounding_box gives the eight corners of the bounding box
    # and each corner is a tuple (x, y, z)

    # The indices of the bottom four corners of the bounding box
    bottom_corners_indices = [0,3,4,7]

    # Initialize sums
    sum_x, sum_y, sum_z = 0, 0, 0

    # Sum up the coordinates of the bottom face corners
    for i in bottom_corners_indices:
        corner = obj.bound_box[i]
        sum_x += corner[0]
        sum_y += corner[1]
        sum_z += corner[2]

    # Calculate average
    avg_x = sum_x / len(bottom_corners_indices)
    avg_y = sum_y / len(bottom_corners_indices)
    avg_z = sum_z / len(bottom_corners_indices)

    # Return the average position as a tuple
    return avg_x, avg_y, avg_z


def average_position_of_top_face(obj):
    # Assuming obj.bounding_box gives the eight corners of the bounding box
    # and each corner is a tuple (x, y, z)

    # The indices of the bottom four corners of the bounding box
    bottom_corners_indices = [1,2,5,6]

    # Initialize sums
    sum_x, sum_y, sum_z = 0, 0, 0

    # Sum up the coordinates of the bottom face corners
    for i in bottom_corners_indices:
        corner = obj.bound_box[i]
        sum_x += corner[0]
        sum_y += corner[1]
        sum_z += corner[2]

    # Calculate average
    avg_x = sum_x / len(bottom_corners_indices)
    avg_y = sum_y / len(bottom_corners_indices)
    avg_z = sum_z / len(bottom_corners_indices)

    # Return the average position as a tuple
    return avg_x, avg_y, avg_z

def average_position_of_front_face(obj):
    # Assuming obj.bounding_box gives the eight corners of the bounding box
    # and each corner is a tuple (x, y, z)

    # The indices of the bottom four corners of the bounding box
    bottom_corners_indices = [0,1,4,5]

    # Initialize sums
    sum_x, sum_y, sum_z = 0, 0, 0

    # Sum up the coordinates of the bottom face corners
    for i in bottom_corners_indices:
        corner = obj.bound_box[i]
        sum_x += corner[0]
        sum_y += corner[1]
        sum_z += corner[2]

    # Calculate average
    avg_x = sum_x / len(bottom_corners_indices)
    avg_y = sum_y / len(bottom_corners_indices)
    avg_z = sum_z / len(bottom_corners_indices)

    # Return the average position as a tuple
    return avg_x, avg_y, avg_z

def make_wireframe(obj):#debug
    obj.hide_render = True
    obj.visible_camera = False
    obj.visible_diffuse = False
    obj.visible_glossy = False
    obj.visible_transmission = False
    obj.visible_volume_scatter = False
    obj.visible_shadow = False
    obj.display_type = 'WIRE'

def make_solid(obj):#debug
    obj.hide_render = True
    obj.visible_camera = False
    obj.visible_diffuse = False
    obj.visible_glossy = False
    obj.visible_transmission = False
    obj.visible_volume_scatter = False
    obj.visible_shadow = False
    obj.display_type = 'SOLID'


class CutFaceOperator(Operator):
    bl_idname = "helmet.cut_face"
    bl_label = "Boolean Front"

    def execute(self, context):
        helmet = bpy.data.objects.get("helmet")
        if helmet:
            # Add a cube
            bpy.ops.mesh.primitive_cube_add(size=2)
            cube = bpy.context.active_object
            cube.name = "cutter"

            # Set cube location and scale
            cube.location = (Vector(get_average_of_negative_y_side(helmet)) + Vector(average_position_of_front_face(helmet))) / 2
            scale_to_bounding_box(cube, helmet)

            cube.scale[2] *= 1.25

            #instead of rotate
            x=cube.scale[0]
            y=cube.scale[1]

            cube.scale[0]=y
            cube.scale[1]=x

            cube.scale[0] *= 1.6

            make_wireframe(cube)
            # Add a Bevel modifier to the cube
            mod_bevel = cube.modifiers.new(name="Bevel", type='BEVEL')
            mod_bevel.width = 0.5  # Adjust bevel width as needed
            mod_bevel.segments = 30  # Adjust number of segments as needed
            mod_bevel.profile = 0.5  # Adjust bevel profile as needed

            # Add a Boolean modifier to the helmet
            mod_bool = helmet.modifiers.new(name="BooleanMod_cut_face", type='BOOLEAN')
            mod_bool.object = cube
            mod_bool.operation = 'DIFFERENCE'
            mod_bool.solver = 'FAST'

        return {'FINISHED'}



class Add_Supports_Operator(Operator):
    bl_idname = "helmet.add_supports"
    bl_label = "Add Support"

    def execute(self, context):
        helmet_front = bpy.data.objects.get("helmet_front")
        helmet_back = bpy.data.objects.get("helmet_back")
        if helmet_front:
            bpy.context.view_layer.objects.active=helmet_front
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
            bpy.context.view_layer.objects.active=helmet_back
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')

            # Add a cube
            #bpy.ops.mesh.primitive_cylinder_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(200, 0.2, 200))
            cylinder = append_and_rename_object(os.path.join(os.path.dirname(__file__),"assets.blend"), 'support', 'cutter')
            cylinder.name = "cutter"

            # Set cube location and scale

            cylinder.location = (Vector(get_average_of_x_side(helmet_front)) + Vector(get_average_of_x_side(helmet_back))) / 2

            #left right switch
            if(bpy.types.Scene.support_right):
                cylinder.location *= Vector((-1,1,1))
                bpy.types.Scene.support_right = False
            else:
                bpy.types.Scene.support_right = True


            bpy.context.space_data.shading.type = 'WIREFRAME'
            bpy.context.space_data.overlay.wireframe_threshold = 0
            make_wireframe(cylinder)

            #removing symetry
            """
            mod_mirror = cylinder.modifiers.new(name="Mirror_support", type='MIRROR')
            mod_mirror.mirror_object = helmet_front
            """
            #add driver
            self.add_driver_to_support(cylinder,"scale",1,"support_length")
            self.add_driver_to_support(cylinder,"scale",0,"support_diameter")
            self.add_driver_to_support(cylinder,"scale",2,"support_diameter")


            refresh_all_properties()




            # Add a Boolean modifier to the helmet
            mod_bool_front = helmet_front.modifiers.new(name="Boolean_cut_support", type='BOOLEAN')
            mod_bool_front.object = cylinder
            mod_bool_front.operation = 'DIFFERENCE'
            mod_bool_front.solver = 'FAST'

            mod_bool_back = helmet_back.modifiers.new(name="Boolean_cut_support", type='BOOLEAN')
            mod_bool_back.object = cylinder
            mod_bool_back.operation = 'DIFFERENCE'
            mod_bool_back.solver = 'FAST'

            self.view_front()
        return {'FINISHED'}



    def add_driver_to_support(self,obj,channel,index,scene_param_name):
        driver = obj.driver_add(channel,index).driver
        if("var" not in [var.name for var in driver.variables]):
            var = driver.variables.new()
        else:
            var=driver.variables["var"]

        #udpate part
        driver.expression="var"
        driver.expression += " "
        driver.expression = driver.expression[:-1]
        #bpy.context.scene.support_length += 1
        #bpy.context.scene.support_length -= 1


        var.type = 'CONTEXT_PROP'
        var.name = "var"

        var.targets[0].data_path = '["'+scene_param_name+'"]'



    def view_front(self):
        # Set the view to front orthographic
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.region_3d.view_perspective = 'ORTHO'
                        space.region_3d.view_rotation = mathutils.Quaternion((1.0, 0.0, 0.0), math.radians(90.0))
                        break

def refresh_all_properties():
    # Get the current scene
    scene = bpy.context.scene

    # Iterate over all properties of the scene
    for prop in dir(scene):
        # Get the property value
        value = getattr(scene, prop)

        # Check if the property is a number and not a boolean
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                # Try to add 1 to the property
                setattr(scene, prop, value + 1)
            except AttributeError:
                # If the property is read-only, skip it
                continue

    # Iterate over all properties of the scene again
    for prop in dir(scene):
        # Get the property value
        value = getattr(scene, prop)

        # Check if the property is a number and not a boolean
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                # Try to subtract 1 from the property
                setattr(scene, prop, value - 1)
            except AttributeError:
                # If the property is read-only, skip it
                continue

class Cut_Mid_Operator(Operator):
    bl_idname = "helmet.cut_mid"
    bl_label = "Cut Middle"

    def execute(self, context):
        helmet = bpy.data.objects.get("helmet")
        if helmet:
            # Add a cube
            bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(200, 0.2, 200))
            cube = bpy.context.active_object
            cube.name = "cutter"

            # Set cube location and scale
            cube.location = get_bounding_box_center_blender(helmet)

            scale_to_bounding_box(cube, helmet)
            cube.scale[1]/=400
            cube.scale*=1.2
            make_wireframe(cube)
            # Add a Bevel modifier to the cube
            mod_bool = helmet.modifiers.new(name="BooleanMod_cut_mid", type='BOOLEAN')
            mod_bool.object = cube
            mod_bool.operation = 'DIFFERENCE'
            mod_bool.solver = 'FAST'

        return {'FINISHED'}

def separate_and_rename_helmet_parts(obj_name):
    # Ensure the object exists and is a mesh
    if obj_name not in bpy.data.objects:
        print(f"Object '{obj_name}' not found")
        return
    obj = bpy.data.objects[obj_name]
    if obj.type != 'MESH':
        print(f"Object '{obj_name}' is not a mesh")
        return

    # Select and activate the object
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.update()

    # Switch to edit mode and separate by loose parts
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

    # Rename and set origin to geometry
    separated_objects = [o for o in bpy.context.selected_objects+[obj] if o != obj]

    # Sort objects based on their Y location
    separated_objects.sort(key=lambda o: o.location.y, reverse=True)

    # Check if there are at least two parts
    if len(separated_objects) < 2:
        print(f"Not enough parts to rename in '{obj_name}'")
        return

    # Rename and set origin
    separated_objects[0].name = 'helmet_front'
    separated_objects[1].name = 'helmet_back'
    for part in separated_objects:
        bpy.context.view_layer.objects.active = part
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

def get_average_of_x_side(obj):
    # Get the 8 corners of the bounding box in local coordinates
    bbox_corners = [Vector(corner) for corner in obj.bound_box]

    # Find the corners with the minimum Y value
    min_x_corners = [corner for corner in bbox_corners if corner.x == min(bbox_corners, key=lambda c: c.x).x]

    # Calculate the average of these corners in local space
    avg_local = sum(min_x_corners, Vector((0,0,0))) / len(min_x_corners)

    # Convert the average point to global coordinates
    avg_global = obj.matrix_world @ avg_local

    return avg_global

def scale_to_bounding_box(source_object, target_object):
    """
    Scale the source object to match the bounding box dimensions of the target object.

    :param source_object: The source Blender object to be scaled.
    :param target_object: The target Blender object to use for scaling dimensions.
    """
    # Ensure both objects are valid Blender objects
    if not isinstance(source_object, bpy.types.Object) or not isinstance(target_object, bpy.types.Object):
        print("Invalid input. Both parameters should be Blender object references.")
        return

    # Get the dimensions of the target object
    target_dimensions = target_object.dimensions

    # Calculate scale factors for each axis
    scale_x = target_dimensions.x / source_object.dimensions.x if source_object.dimensions.x != 0 else 0
    scale_y = target_dimensions.y / source_object.dimensions.y if source_object.dimensions.y != 0 else 0
    scale_z = target_dimensions.z / source_object.dimensions.z if source_object.dimensions.z != 0 else 0

    # Scale the source object to match the target object's dimensions
    source_object.scale = (scale_x, scale_y, scale_z)

def get_average_of_negative_y_side(obj):
    # Get the 8 corners of the bounding box in local coordinates
    bbox_corners = [Vector(corner) for corner in obj.bound_box]

    # Find the corners with the minimum Y value
    min_y_corners = [corner for corner in bbox_corners if corner.y == min(bbox_corners, key=lambda c: c.y).y]

    # Among the min Y corners, find the two with the minimum Z values
    min_y_min_z_corners = sorted(min_y_corners, key=lambda c: c.z)[:2]

    # Calculate the average of these two corners in local space
    avg_local = sum(min_y_min_z_corners, Vector((0,0,0))) / 2

    # Convert the average point to global coordinates
    avg_global = obj.matrix_world @ avg_local

    return avg_global



addon_name = __name__.partition('_')[0]

def draw_call_settings_button(layout):
    layout.operator(
                "preferences.addon_show", icon="SETTINGS"
            ).module = __package__

def get_prefs():
    return bpy.context.preferences.addons[addon_name].preferences

def get_MaxSize(self):
    max_size = max( self.dimensions )
    return max_size

def set_MaxSize(self, value):
    max_size = max( self.dimensions )
    if value!=0:
        k = max_size / value
        if k!=0:
            self.scale[0] = self.scale[0] / k
            self.scale[1] = self.scale[1] / k
            self.scale[2] = self.scale[2] / k

            for obj in bpy.context.selected_objects:
                if hasattr(obj, "scale")==True and obj is not self:
                    obj.scale[0] = obj.scale[0] / k
                    obj.scale[1] = obj.scale[1] / k
                    obj.scale[2] = obj.scale[2] / k

    return None

def get_pdimensions(self):
    return self.dimensions

def set_pdimensions(self, value):
    if value is not None:
        k=0
        if self.dimensions[0]!=value[0]:
            k = self.dimensions[0] / value[0]
        elif self.dimensions[1]!=value[1]:
            k = self.dimensions[1] / value[1]
        elif self.dimensions[2]!=value[2]:
            k = self.dimensions[2] / value[2]

        if k!=0:
            self.scale[0] = self.scale[0] / k
            self.scale[1] = self.scale[1] / k
            self.scale[2] = self.scale[2] / k

            for obj in bpy.context.selected_objects:
                if hasattr(obj, "scale")==True and obj is not self:
                    obj.scale[0] = obj.scale[0] / k
                    obj.scale[1] = obj.scale[1] / k
                    obj.scale[2] = obj.scale[2] / k

    return None


class STEP0_PT_Panel(Panel):
    """Panel Proportional Dimensions to new Size"""
    bl_idname = "STEP0_PT_Panel"
    bl_label = "Step 0: Import"
    bl_parent_id = 'MAIN_PT_Panel'
    bl_order = 0
    #bl_options = {"DEFAULT_CLOSED"}

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Helmet"

    def draw(self, context):
        layout = self.layout
        row=layout.row()
        row.operator("helmet.set_unit_scale")
        row=layout.row()
        row.operator("helmet.import_stl", text="Import STL")

class PROPORTIONALDIMENSIONSTO_PT_MaxSize(Panel):
    """Panel Proportional Dimensions to new Size"""
    bl_idname = "PROPORTIONALDIMENSIONSTO_PT_MaxSize"
    bl_label = "Proportional Dimensions"
    bl_parent_id = 'MAIN_PT_Panel'
    bl_order = 0
    #bl_options = {"DEFAULT_CLOSED"}

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Helmet"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        layout = self.layout

        helmet = [obj for obj in bpy.data.objects if "helmet" == obj.name]#zeg changed
        if helmet:
            helmet = helmet[0]
            max_size = max(context.active_object.dimensions)
            row = layout.row(align=True)
            split = row.split(factor=0.8)
            split.column().prop(helmet, 'pdimensions', text="Proportional Dimensions")
            col1 = split.column()
            col1.scale_y = .9
            col1.row().label(text="")
            col1.row().operator("proportionaldimensionsto.setx1", text="1")
            col1.row().operator("proportionaldimensionsto.sety1", text="1")
            col1.row().operator("proportionaldimensionsto.setz1", text="1")

            row = layout.row(align=True)
            split = row.split(factor=0.8)
            split.column().prop(helmet, 'MaxSize')
            col1 = split.column()
            col1.scale_y = 1
            col1.row().operator("proportionaldimensionsto.setmaxsize1", text="1")

        else:
            row = layout.row(align=True)
            split = row.split(factor=0.8)
            split.column().label(text="")
            col1 = split.column()
            col1.scale_y = .9
            col1.row().label(text="")
            col1.row().label(text=" ")
            col1.row().label(text=" ")
            col1.row().label(text=" ")

            row = layout.row(align=True)
            split = row.split(factor=0.8)
            split.column().label(text="")
            col1 = split.column()
            col1.scale_y = 1
            col1.row().label(text="")

        layout.row().operator("helmet.apply_modifiers")



class PROPORTIONALDIMENSIONSTO_OP_SetX1(bpy.types.Operator):
    """Set object dimension X=1"""
    bl_idname = "proportionaldimensionsto.setx1"
    bl_label  = "Set object's dimension X=1"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        res = False
        if context.mode=='OBJECT' and context.active_object is not None and hasattr(context.active_object, "dimensions")==True:
            res = True
        return res

    def execute(self, context):
        ob = context.active_object
        ob.pdimensions[0]=1.0
        return {"FINISHED"}

class PROPORTIONALDIMENSIONSTO_OP_SetY1(bpy.types.Operator):
    """Set object dimension Y=1"""
    bl_idname = "proportionaldimensionsto.sety1"
    bl_label  = "Set object's dimension Y=1"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        res = False
        if context.mode=='OBJECT' and context.active_object is not None and hasattr(context.active_object, "dimensions")==True:
            res = True
        return res

    def execute(self, context):
        ob = context.active_object
        ob.pdimensions[1]=1.0
        return {"FINISHED"}

class PROPORTIONALDIMENSIONSTO_OP_SetZ1(bpy.types.Operator):
    """Set object dimension Z=1"""
    bl_idname = "proportionaldimensionsto.setz1"
    bl_label  = "Set object's dimension Z=1"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        res = False
        if context.mode=='OBJECT' and context.active_object is not None and hasattr(context.active_object, "dimensions")==True:
            res = True
        return res

    def execute(self, context):
        ob = context.active_object
        ob.pdimensions[2]=1.0
        return {"FINISHED"}

class PROPORTIONALDIMENSIONSTO_OP_SetMaxSize1(bpy.types.Operator):
    """Set object's max dimension =1"""
    bl_idname = "proportionaldimensionsto.setmaxsize1"
    bl_label  = "Set object's max dimension =1"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        res = False
        if context.mode=='OBJECT' and context.active_object is not None and hasattr(context.active_object, "dimensions")==True:
            res = True
        return res

    def execute(self, context):
        ob = context.active_object
        ob.MaxSize=1.0
        return {"FINISHED"}

def append_and_rename_object(blend_file_path, object_name, new_name, link=False):
    """
    Appends an object from a specified .blend file into the current Blender file, renames it, and returns it.

    :param blend_file_path: The path to the .blend file.
    :param object_name: The name of the object to append.
    :param new_name: The new name for the appended object.
    :param link: If True, link the object instead of appending. Defaults to False.
    :return: The appended and renamed object, or None if not found.
    """
    # Check if the .blend file exists
    if not os.path.exists(blend_file_path):
        print(f"Blend file not found: {blend_file_path}")
        return None

    # Append or link the object
    bpy.ops.wm.append(
        filepath=os.path.join(blend_file_path, "Object", object_name),
        directory=os.path.join(blend_file_path, "Object"),
        filename=object_name,
        link=link
    )

    # Rename the object and return it
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(object_name):
            obj.name = new_name
            return obj

    return None



def register_maxsize():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_object_props(3)

def unregister_maxsize():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


classes = (PROPORTIONALDIMENSIONSTO_PT_MaxSize,
    PROPORTIONALDIMENSIONSTO_OP_SetX1,PROPORTIONALDIMENSIONSTO_OP_SetY1,PROPORTIONALDIMENSIONSTO_OP_SetZ1,
    PROPORTIONALDIMENSIONSTO_OP_SetMaxSize1,
    )

def register_object_props(precision):
    bpy.types.Object.pdimensions = FloatVectorProperty(name="pdimensions", description="Max size by axis X/Y/Z", get=get_pdimensions, set=set_pdimensions, subtype="XYZ_LENGTH", precision=precision)
    bpy.types.Object.MaxSize     = FloatProperty(name="Max Size", description="Max size of object", get=get_MaxSize, set=set_MaxSize, unit="LENGTH", precision=precision)

def update_types(self, context):
    pref = get_prefs()
    precision = 3
    register_object_props(precision)


def register():

    bpy.utils.register_class(MAIN_PT_Panel)
    bpy.utils.register_class(STEP0_PT_Panel)
    bpy.utils.register_class(JIC_PT_Panel)
    register_maxsize()
    bpy.utils.register_class(STEP1_PT_Panel)
    bpy.utils.register_class(STEP2_PT_Panel)
    bpy.utils.register_class(STEP3_PT_Panel)
    bpy.utils.register_class(import_stl)
    bpy.utils.register_class(SolidifyObjectOperator)
    bpy.utils.register_class(CutBottomHalfOperator)
    bpy.utils.register_class(Cut_Mid_Operator)
    bpy.utils.register_class(ExportSTLOperator)
    bpy.utils.register_class(ApplyModifiersOperator)
    bpy.utils.register_class(Show_Head_Operator)
    bpy.utils.register_class(Hide_Head_Operator)
    bpy.utils.register_class(Set_Unit_Scale_Operator)
    bpy.utils.register_class(CutEarOperator)
    bpy.utils.register_class(Add_Supports_Operator)
    bpy.utils.register_class(Hinge_Add_Operator)
    bpy.utils.register_class(CutFaceOperator)
    bpy.utils.register_class(Decimate_Object_Operator)
    bpy.utils.register_class(Show_Backup_Operator)
    bpy.types.Scene.solidify_thickness = FloatProperty(name="Solidify Thickness", default=6.4)
    bpy.types.Scene.hinge_size_x = FloatProperty(name="hinge_size_x", default=16)
    bpy.types.Scene.hinge_size_y = FloatProperty(name="hinge_size_y", default=30)
    bpy.types.Scene.hinge_diameter = FloatProperty(name="hinge_diameter", default=2.0)
    bpy.types.Scene.support_diameter = FloatProperty(name="support_diameter", default=2)
    bpy.types.Scene.support_length = FloatProperty(name="support_length", default=20)
    bpy.types.Scene.support_right = BoolProperty(name="support_right", default=False)
    #bpy.types.Scene.decimate_factor = FloatProperty(name="decimate_factor", default=0.5)
    bpy.types.Scene.decimate_factor = bpy.props.FloatProperty(
        name="Decimate Factor",
        default=0.5,  # Set your default value here
        min=0.0,
        max=1.0,
        step=0.1,  # Set your desired step value here
    )
    bpy.types.Scene.hinge_height = bpy.props.FloatProperty(
        name="Hinge Height",
        default=1   ,  # Set your default value here
        min=0.0,
        max=10,
        step=0.1,  # Set your desired step value here
    )
    bpy.types.Scene.hinge_resolution_x = bpy.props.IntProperty(
        name="hinge resolution x",
        default=5   ,  # Set your default value here
        min=2,
        max=20,
        step=1,  # Set your desired step value here
    )
    bpy.types.Scene.hinge_resolution_y = bpy.props.IntProperty(
        name="hinge resolution y",
        default=8   ,  # Set your default value here
        min=2,
        max=20,
        step=1,  # Set your desired step value here
    )
    bpy.types.Scene.hinge_bottom_scale = bpy.props.FloatProperty(
        name="hinge bottom scale",
        default=1.272152   ,  # Set your default value here
        min=1,
        max=3,
        step=1,  # Set your desired step value here
    )
    bpy.types.Scene.hinge_edge_offset = bpy.props.FloatProperty(
        name="hinge wall thickness",
        default=1.72   ,  # Set your default value here
        min=0,
        max=10,
        step=1,  # Set your desired step value here
    )
    bpy.types.Scene.hinge_hole_dept = bpy.props.FloatProperty(
        name="hinge connector height",
        default=-7.396    ,  # Set your default value here
        min=-20,
        max=0,
        step=1,  # Set your desired step value here
    )
    bpy.types.Scene.hinge_holder_obj_marigin = bpy.props.FloatProperty(
        name="hinge tolerances",
        default=0.079    ,  # Set your default value here
        min=0,
        max=1,
        step=1,  # Set your desired step value here
    )
    bpy.types.Scene.hinge_bottom_bury_offset = bpy.props.FloatProperty(
        name="hinge bottom bury offset",
        default=1.2    ,  # Set your default value here
        min=0,
        max=4,
        step=1,  # Set your desired step value here
    )
def unregister():
    bpy.utils.unregister_class(MAIN_PT_Panel)
    unregister_maxsize()
    bpy.utils.unregister_class(STEP0_PT_Panel)
    bpy.utils.unregister_class(JIC_PT_Panel)
    bpy.utils.unregister_class(STEP1_PT_Panel)
    bpy.utils.unregister_class(STEP2_PT_Panel)
    bpy.utils.unregister_class(STEP3_PT_Panel)
    bpy.utils.unregister_class(import_stl)
    bpy.utils.unregister_class(SolidifyObjectOperator)
    bpy.utils.unregister_class(ExportSTLOperator)
    bpy.utils.unregister_class(Cut_Mid_Operator)
    bpy.utils.unregister_class(CutBottomHalfOperator)
    bpy.utils.unregister_class(ApplyModifiersOperator)
    bpy.utils.unregister_class(Set_Unit_Scale_Operator)
    bpy.utils.unregister_class(Show_Head_Operator)
    bpy.utils.unregister_class(CutEarOperator)
    bpy.utils.unregister_class(Hide_Head_Operator)
    bpy.utils.unregister_class(Add_Supports_Operator)
    bpy.utils.unregister_class(CutFaceOperator)
    bpy.utils.unregister_class(Hinge_Add_Operator)
    bpy.utils.unregister_class(Decimate_Object_Operator)
    del bpy.types.Scene.solidify_thickness
    del bpy.types.Scene.decimate_factor
    del bpy.types.Scene.support_diameter
    del bpy.types.Scene.support_length
    del bpy.types.Scene.hinge_diameter
    del bpy.types.Scene.support_right
    del bpy.types.Scene.hinge_height
    del bpy.types.Scene.hinge_resolution_x
    del bpy.types.Scene.hinge_resolution_y
    del bpy.types.Scene.hinge_bottom_scale
    del bpy.types.Scene.hinge_edge_offset
    del bpy.types.Scene.hinge_hole_dept
    del bpy.types.Scene.hinge_holder_obj_marigin
    del bpy.types.Scene.hinge_bottom_bury_offset

if __name__ == "__main__":
    register()
