import json, re

class Loader:
    def loadJsonFromText(text : str):
        # print(text)
        # results = re.findall(r'\{.*?\}', text)


        # print(results)
        # for res in results:
        prop = text
        arr = prop.split("{",1)
        if len(arr) > 1:
            prop = "{" + arr[1]
            for i in range(len(prop)):
                val = len(prop) - 1 - i
                if prop[val] == "}":
                    prop = prop[:val] + "}"
                    break
        else:
            print('Can\'t find json object in txt')
            return False, None
        # print(prop)
        try:
            val = json.loads(prop, strict=False)
            return True, val
        except:
            pass

        print('Can\'t find json object in txt')
        return False, None
