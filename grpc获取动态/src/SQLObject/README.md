**[gen_model](./gen_model.py) 生成SQLAlchemy模型**
>
> 使用前，需要将里面的sql连接修改成同步的pymysql之类的，然后直接使用即可 \
> 使用之后，需要到[models](./models.py)里面，将以下这段代码替换进去，目的在于告诉sqlalchemy这两个模型是一对一，不是一对多。
> ```python
> bilidyndetail: Mapped['Bilidyndetail'] = relationship('Bilidyndetail', uselist=True, back_populates='lot')```

