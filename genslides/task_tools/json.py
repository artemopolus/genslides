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
    jres, data, jreport = Loader.loadJsonFromTextStr( data_str )
    if jres:
        return Loader.convJsonToText(filterUsingExpressions( expression, data))
    else:
        logger.debug("Error json conv: %s \n\n\nsrc:\n\n %s", jreport, data_str)
    return ""