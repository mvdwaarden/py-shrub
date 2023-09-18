import xmlschema
from archi_model.model.meta_model import MetaModel, MetaClass, MetaRelation, \
    MetaAttribute, MetaStringAttributeType
import archi_util.core.logging as logging


def model_read_from_xsd(name: str, xml: str) -> MetaModel:
    meta_model = MetaModel(name)
    schema = xmlschema.XMLSchema(xml)
    for complex_type in schema.complex_types:
        model_add_complex_type(meta_model, complex_type, complex_type.name)
    for root in schema.root_elements:
        if root.type.is_complex():
            model_add_complex_type(meta_model, root.type, root.name)

    return meta_model


def model_add_complex_type(meta_model: MetaModel, complex_type, name: str) -> MetaClass:
    mc = meta_model.find_class_by_name(name)
    if mc is not None:
        return mc
    mc = MetaClass(name)
    meta_model.add_meta_class(mc)
    for attribute in complex_type.attributes:
        mc.add_attribute(MetaAttribute(attribute.name, MetaStringAttributeType))
    for element in complex_type.content.iter_elements():
        if element.type.is_simple():
            mc.add_attribute(MetaAttribute(element.name, MetaStringAttributeType))
        elif element.type.is_complex() and element.type.has_simple_content():
            mc.add_attribute(MetaAttribute(element.name, MetaStringAttributeType))
        elif element.type.is_complex():
            if element.type.name is None:
                name = element.name
            else:
                name = element.type.name
            mc_target = model_add_complex_type(meta_model, element.type, name)

            mc_target = meta_model.find_class_by_name(name)

            if mc_target is None:
                mc_target = MetaClass(name)
                meta_model.add_meta_class(mc_target)
            relation = MetaRelation(element.name, f"reverse_{element.name}", mc, mc_target)
            meta_model.add_relation(relation)
    return mc