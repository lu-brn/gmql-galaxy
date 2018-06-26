# gmql-galaxy
A set of galaxy tools to write GMQL queries through a visual interface and integrate their execution with pre-existing 
genomic analysis workflows.

## Setup

### Galaxy Tool Shed

These tools are available on the Galaxy Tool Shed. They can be installed individually or all together thought 
the suite_gmql_galaxy. We recommed this second option.

### Manually

It is possible to manually install these tools as well (for instance, for development). 

1. Download this repository in a chosen destination. 
```
git clone https://github.com/lu-brn/gmql-galaxy.git
```
2. Locate your galaxy installation folder and move the gmql_galaxy folder in **galaxy/tools**.
3. Copy the content of **tool_conf.xml** into **galaxy/config/tool_conf.xml**
4. Copy the **gmql.py** file in **galaxy/lib/galaxy/datatypes**
5. Copy the content of **datatypes_conf.xml** in **galaxy/config/datatypes_conf.xml**
