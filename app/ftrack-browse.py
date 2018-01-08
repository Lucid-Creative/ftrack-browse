'''
ftrack browser

KBjordahl
Lucid
100517

currently just at ttk.Treeview test
'''


import Tkinter
import ttk
import os
import logging, logging.config
from collections import defaultdict


import ftrack_api

limit=500

class Browser(ttk.Frame):


    def __init__(self, master):

        ttk.Frame.__init__(self, master)

        logger = logging.getLogger(__name__)

        self.objects = defaultdict()

        logger.info("Setting up GUI widgets")
        self._init_widgets()

        # set up from ENV 
        logger.info("Logging into ftrack from ENV vars")
        self.ftrack = ftrack_api.Session()

        self.populate_top_level()

    def _init_widgets(self):
        '''
        sets up the widgets
        '''
        logger = logging.getLogger(__name__)

        # treeview
        self.tree = ttk.Treeview(self, columns=('data',))
        self.tree.pack(fill=Tkinter.BOTH, expand=True)
        # column headers
        self.tree.column('data', width=100, anchor=Tkinter.W)
        self.tree.heading('data', text="Value")
        # alt row coloring
        self.tree.tag_configure('oddrow', background='azure2')
        logger.debug("Treeview complete.")

        # event to load on open
        self.tree.bind('<<TreeviewOpen>>', self.load_children)

        # pack self
        self.pack(fill=Tkinter.BOTH, expand=True)


    def populate_top_level(self):
        '''
        populates the top level of nodes in the tree
        '''
        logger = logging.getLogger(__name__)
        logger.info("Creating top level nodes...")
        # top level nodes are the types from ftrack
        type_list = self.ftrack.types.keys()
        for counter, entity_type in enumerate(sorted(type_list)):
            # for limiting
            if counter > limit: break
            
            logger.debug("Building node %d/%d: %s",counter, len(type_list), entity_type)
            # node for the type
            try:
                # for alt row coloring
                if counter % 2 == 0: tags=('oddrow',) 
                else: tags=(None,)
                self.tree.insert("", "end", entity_type, text=entity_type, tags=tags)
                logger.debug("Added node for %s", entity_type)
                logger.debug("Getting list of %s from ftrack", entity_type)
                ftrack_entities = self.ftrack.query("{}".format(entity_type)).all()
                self.populate_branch(entity_type, ftrack_entities)
            except:
                logger.error("Couldn't add %s", entity_type, exc_info=True)
            # now get a list of everything of this type and populate the branch
            
        logger.info("...top level nodes complete!")
        
    def load_children(self, event):
        logger = logging.getLogger(__name__)

        iid = self.tree.focus()
        logger.debug("Opened: %s", iid)

        children = self.tree.get_children(item=iid)
        logger.debug("Children:\n %s", children)

        if children[0].endswith("dummy"):
            logger.info("Loading children of %s from %s", iid, self.objects[iid])
            try:
                self.populate_branch(iid, self.objects[iid], remove_dummy=True)
            except:
                logger.error("Couldn't populate entities!", exc_info=True)


    def populate_branch(self, parent_node_id, iterable, remove_dummy=False):
        '''
        adds items to a branch.

        ### Args:
        - **parent_node_id**: string for the *ttk.Treeview* item id to use as the parent
        - **ftrack_type**: string of the type to retrieve from ftrack
        '''
        logger = logging.getLogger(__name__)

        # in case we have a dict like object
        if hasattr(iterable, 'items'):
            logger.debug("Using dict mode for %s", iterable)
            try:
                iterable = iterable.items()
            except:
                logger.warn("Couldn't switch to dict mode.", exc_info=True)

        logger.info("Populating branch '%s' with %d items", parent_node_id, len(iterable))
        for counter, entity in enumerate(iterable):
            # for limiting
            if counter > limit: break

            # for alt row coloring
            if counter % 2 == 0: tags=('oddrow',) 
            else: tags=(None,)

            # if we have a dict as an iterable, the entities will be key value pairs
            if isinstance(entity, tuple):
                entity, value = entity
                obj = value
            else:
                value = ""
                obj = entity

            logger.debug("->Creating entity %d/%d: %s %s %s (%r)", counter+1, len(iterable), 
                entity, "=" if value <> "" else "", value, obj)
            try:
                node_id = "{}::{}".format(parent_node_id, entity)
                # store the object of the entity in the objects dict
                logger.debug("--> Storing object at %s", node_id)
                self.objects[node_id] = obj

                self.tree.insert(parent_node_id, "end", node_id, 
                    text="{}".format(entity), 
                    values=(value,),
                    tags=tags
                    )
                logger.debug("--> Inserted entity node in tree")
            except:
                logger.error("Couldn't make entity: %s", entity, exc_info=True)

            # let's see if we can iterate on the value, if so, make children
            if hasattr(obj, '__iter__'):
                try:
                    iter_key = "{}::dummy".format(node_id)
                    self.tree.insert(node_id,"end",iter_key, text="Loading...")
                    logger.debug("--> Added dummy node to %s", entity)
                except:
                    logger.error("Couldn't add dummy child to %s", entity, exc_info=True)
                    
        # remove dummy entry
        if remove_dummy:
            self.tree.delete("{}::dummy".format(parent_node_id))

logging_config = dict(
    version=1,
    disable_existing_loggers= False,
    formatters= {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    loggers= {
        'ftrack_api':{
            'handlers': ['console'],
            'level': 'INFO',
        },
        'urllib3':{
            'handlers': ['console'],
            'level': 'INFO',
        },
        '':{
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
)

def main():

    logging.config.dictConfig(logging_config)

    root = Tkinter.Tk()
    app = Browser(root)
    root.mainloop()

if __name__ == '__main__':
    main()