import random
import Orange
data = Orange.data.Table("lenses")
id = Orange.data.new_meta_id()
for inst in data:
    inst[id] = random.random()
print data[0]
