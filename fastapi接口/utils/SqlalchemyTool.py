def sqlalchemy_model_2_dict(instance):
    return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}
