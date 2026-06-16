import jmespath
from genslides.utils.loader import Loader
import logging

logger = logging.getLogger(__name__)



def filterUsingExpressions( expression : str, data  ):
    if isinstance( data , dict):
        return jmespath.search(expression, data)
    else:
        logger.debug("Not dict")
    return ""

def filterUsingParameters( params : dict ):
    expression = params.get("expression","")
    data_str = params.get("target","")
    key_str = params.get("key","")
    jres, data, jreport = Loader.loadJsonFromTextStr( data_str )
    if jres:
        filtered = filterUsingExpressions( expression, data ) 
        output = filtered if key_str == "" else {key_str:filtered}
        return Loader.convJsonToText(output)
    else:
        logger.debug("Error json conv: %s \n\n\nsrc:\n\n %s", jreport, data_str)
    return ""