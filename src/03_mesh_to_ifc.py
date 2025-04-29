import ifcopenshell
import ifcopenshell.guid

def read_parsed_mesh_file(path):
    """
    Reads a mesh file (assuming OBJ-like format with 'v ' and 'f ' lines).
    Returns (vertices, faces) where vertices is a list of (x, y, z) tuples and
    faces is a list of lists of vertex indices (1-based as in OBJ files).
    """
    vertices = []
    faces = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("v "):  # vertex line
                parts = line.split()
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                vertices.append((x, y, z))
            elif line.startswith("f "):  # face line
                parts = line.split()
                # If OBJ contains texture/normal data (e.g. "f 1/1/1 2/2/2 ..."), use only the vertex index.
                indices = [int(p.split('/')[0]) for p in parts[1:]]
                faces.append(indices)
    return vertices, faces

def create_ifc_from_mesh(verts, faces, output_ifc="GeneratedBlock.ifc"):
    # Create a new IFC file with the IFC2X3 schema
    ifc_file = ifcopenshell.file(schema="IFC2X3")
    
    # --- Create basic OwnerHistory information (using IFC2X3 attributes) ---
    # In IFC2X3, IfcPerson does not use an 'Identification' attribute.
    person = ifc_file.create_entity("IfcPerson", FamilyName="Smith", GivenName="User1")
    organization = ifc_file.create_entity("IfcOrganization", Name="DefaultOrg")
    person_and_org = ifc_file.create_entity("IfcPersonAndOrganization", ThePerson=person, TheOrganization=organization)
    application = ifc_file.create_entity("IfcApplication",
                                         ApplicationDeveloper=organization,
                                         Version="1.0",
                                         ApplicationFullName="MeshToIFC",
                                         ApplicationIdentifier="MESHIFC")
    owner_history = ifc_file.create_entity("IfcOwnerHistory",
                                           OwningUser=person_and_org,
                                           OwningApplication=application,
                                           ChangeAction="ADDED",
                                           CreationDate=1622499200)
    
    # --- Create a basic Unit Assignment for IFC2X3 ---
    si_length = ifc_file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    si_area = ifc_file.create_entity("IfcSIUnit", UnitType="AREAUNIT", Name="SQUARE_METRE")
    si_volume = ifc_file.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT", Name="CUBIC_METRE")
    unit_assignment = ifc_file.create_entity("IfcUnitAssignment", Units=[si_length, si_area, si_volume])
    
    # --- Create the Geometric Representation Context ---
    origin = ifc_file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    axis2placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=origin)
    geom_context = ifc_file.create_entity("IfcGeometricRepresentationContext",
                                          ContextIdentifier="Body",
                                          ContextType="Model",
                                          CoordinateSpaceDimension=3,
                                          Precision=0.001,
                                          WorldCoordinateSystem=axis2placement)
    
    # --- Build the Spatial Structure ---
    project = ifc_file.create_entity("IfcProject",
                                     GlobalId=ifcopenshell.guid.new(),
                                     OwnerHistory=owner_history,
                                     Name="LLM Mesh Project",
                                     UnitsInContext=unit_assignment)
    site = ifc_file.create_entity("IfcSite",
                                  GlobalId=ifcopenshell.guid.new(),
                                  OwnerHistory=owner_history,
                                  Name="Site")
    building = ifc_file.create_entity("IfcBuilding",
                                      GlobalId=ifcopenshell.guid.new(),
                                      OwnerHistory=owner_history,
                                      Name="MyBuilding")
    storey = ifc_file.create_entity("IfcBuildingStorey",
                                    GlobalId=ifcopenshell.guid.new(),
                                    OwnerHistory=owner_history,
                                    Name="GroundFloor")
    
    def create_default_local_placement(relative_to=None):
        point = ifc_file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
        placement = ifc_file.create_entity("IfcAxis2Placement3D", Location=point)
        return ifc_file.create_entity("IfcLocalPlacement", PlacementRelTo=relative_to, RelativePlacement=placement)
    
    # Create placements for spatial elements
    site.ObjectPlacement = create_default_local_placement()
    building.ObjectPlacement = create_default_local_placement(site.ObjectPlacement)
    storey.ObjectPlacement = create_default_local_placement(building.ObjectPlacement)
    
    # Aggregate the spatial structure
    ifc_file.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(),
                           OwnerHistory=owner_history,
                           RelatingObject=project,
                           RelatedObjects=[site])
    ifc_file.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(),
                           OwnerHistory=owner_history,
                           RelatingObject=site,
                           RelatedObjects=[building])
    ifc_file.create_entity("IfcRelAggregates", GlobalId=ifcopenshell.guid.new(),
                           OwnerHistory=owner_history,
                           RelatingObject=building,
                           RelatedObjects=[storey])
    
    # --- Build a faceted BRep from the mesh data ---
    face_entities = []
    for face in faces:
        # Adjust 1-indexed OBJ face indices to 0-indexed Python list indices.
        poly_points = [ifc_file.create_entity("IfcCartesianPoint", Coordinates=verts[idx - 1]) for idx in face]
        poly_loop = ifc_file.create_entity("IfcPolyLoop", Polygon=poly_points)
        face_bound = ifc_file.create_entity("IfcFaceBound", Bound=poly_loop, Orientation=True)
        face_entity = ifc_file.create_entity("IfcFace", Bounds=[face_bound])
        face_entities.append(face_entity)
    closed_shell = ifc_file.create_entity("IfcClosedShell", CfsFaces=face_entities)
    faceted_brep = ifc_file.create_entity("IfcFacetedBrep", Outer=closed_shell)
    
    shape_rep = ifc_file.create_entity("IfcShapeRepresentation",
                                       ContextOfItems=geom_context,
                                       RepresentationIdentifier="Body",
                                       RepresentationType="FacetedBrep",
                                       Items=[faceted_brep])
    prod_def_shape = ifc_file.create_entity("IfcProductDefinitionShape", Representations=[shape_rep])
    
    # --- Create a local placement for the building element (relative to the storey) ---
    element_placement = create_default_local_placement(storey.ObjectPlacement)
    
    # --- Create the building element (using IfcBuildingElementProxy) ---
    # Note: PredefinedType is not available in IFC2X3 for IfcBuildingElementProxy.
    element = ifc_file.create_entity("IfcBuildingElementProxy",
                                     GlobalId=ifcopenshell.guid.new(),
                                     OwnerHistory=owner_history,
                                     Name="GeneratedBlock",
                                     ObjectPlacement=element_placement,
                                     Representation=prod_def_shape)
    
    # Link the element into the spatial structure (storey containment)
    ifc_file.create_entity("IfcRelContainedInSpatialStructure",
                           GlobalId=ifcopenshell.guid.new(),
                           OwnerHistory=owner_history,
                           RelatingStructure=storey,
                           RelatedElements=[element])
    
    # Write out the IFC file (header will now indicate IFC2X3)
    ifc_file.write(output_ifc)
    print("IFC file written to", output_ifc)

def main():
    verts, faces = read_parsed_mesh_file("llama-mesh_obj.obj")
    create_ifc_from_mesh(verts, faces, output_ifc="GeneratedBlock.ifc")

if __name__ == "__main__":
    main()
