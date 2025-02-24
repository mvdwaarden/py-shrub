# Archi Shrubbery

## Prerequisites
Use python 3.12 or newer

Use virtual environments (see main ../README.md)

## Archi use cases

### 10 Step workflow for detached edit, with entity resolution merge, and back import
Check : https://forum.archimatetool.com/index.php?topic=161.0 
 
- From Archi : export to XMI [1]
- With shrub_archi: Extract view for edit [2]
- ``` python -m shrub_archi.main -config-ini ./data/shrub_archi/config.ini -archi extract -source "source file.xml" -purpose "selected for detached edit" ```
- From Archi: import XMI [3]
- With Archi: Edit model [4]
- From Archi: export XMI [5]
- With shrub_archi: merge XMI back into exported XMI from [1] [6]
- ``` python -m shrub_archi.main  -config-ini ./data/shrub_archi/config.ini -archi merge -source "source file.xml" -target "target file.xml" -resolutions resolutions -workdir "some workdir" ```
- With shrub_archi: Extract View for merge [7]  
- ``` python -m shrub_archi.main -config-ini ./data/shrub_archi/config.ini -archi extract -source "source file.xml" -purpose "selected for merge" ```
- From Archi: import XMI as new model [8]
- From Archi: save new model as .archimate [9]
- From Archi: import into existing big Archi model [10]

## Entity resolution overview

![entity resolution](./doc/images/Entity%20Resolution.svg)