from nltk.corpus import wordnet

# wordnet will match just about any one or two character string, so
# instead I use a more restrictive list of words for shorter strings.
short_words = set(['a', 'i', 'o', 'be', 'ms', 'gd', 'it', 'pa', 'tb', 'ar', 'ty', 'ho', 'kw', 'hg', 'au', 'kr', 'tl', 'cs', 'on', 'mn', 'it', 'la', 'eh', 'mr', 'am', 'va', 'in', 'go', 'ah', 'tc', 'oh', 'er', 'sr', 're', 'ex', 'cu', 'br', 'mt', 'be', 'si', 'ay', 'lo', 'sn', 'ha', 'di', 'ax', 'mo', 'ca', 'hi', 'cl', 'se', 'ge', 'no', 'rn', 'ba', 'lr', 'rx', 'fe', 'hf', 'pl', 'lu', 'pb', 'or', 'ne', 'pa', 'st', 'sc', 'al', 'jo', 'nd', 'by', 'kc', 'so', 'em', 'rb', 'ts', 'io', 'as', 'us', 'mg', 'hz', 'cm', 'he', 'ho', 'pd', 'ci', 'xe', 'db', 'wm', 'of', 'rh', 'sm', 'he', 'an', 'ms', 'ye', 'bi', 'as', 'pi', 'dr', 'oz', 'mu', 'np', 'am', 'nu', 'pu', 'ln', 'cd', 'vs', 'gs', 'is', 'zn', 'do', 'we', 'if', 'pm', 'ed', 'at', 'po', 'co', 'ta', 'cf', 'mb', 'wu', 'ph', 'lt', 'ks', 'at', 'ni', 'la', 'rd', 'uh', 'up', 'ob', 'ra', 'ru', 'ti', 'bk', 'na', 'sq', 'ok', 'fa', 'ox', 'ad', 'ti', 'um', 'sh', 'ir', 'to', 'yb', 'av', 'ls', 're', 'ge', 'md', 'fm', 'li', 'nb', 'yo', 'ga', 'fr', 'os', 'sb', 'me', 'th', 'tm', 'ow', 'mi', 'eu', 'cs', 'in', 'ac', 'my', 'id', 'jr', 'ag', 'rs', 'le', 'ur', 'ma', 'cr', 'es', 'zr', 'pt', 'es'])

class SegmentString:

    def __init__(self,):
        self._memoize = dict()

    def string_segments(self, input_string):
        if len(input_string) < 3 and input_string in short_words:
            return input_string
        elif len(input_string) > 2 and wordnet.synsets(input_string):
            return input_string
        if input_string in self._memoize:
            return self._memoize[input_string]
        
        for i in range(1, len(input_string)):
            prefix = input_string[:i]
            if ((len(input_string) < 3 and input_string in short_words) or
                len(prefix) > 2 and wordnet.synsets(prefix)):
                suffix = input_string[i:]
                suffix_segmentation = self.string_segments(suffix)
                if suffix_segmentation:
                    self._memoize[input_string] = prefix + " " + suffix_segmentation
                    return prefix + " " + suffix_segmentation
        self._memoize[input_string] = False
        return False


# uncomment these lines to play around with it.
# print(segment.string_segments("catcatdogdotcat"))
