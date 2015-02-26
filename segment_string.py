class StringSegment:

    def __init__(self):
        self._memoize = dict()

    def string_segments(self, input_string, dictionary):
        if input_string in dictionary:
            return input_string
        if input_string in self._memoize:
            return self._memoize[input_string]
        
        for i in range(1, len(input_string)):
            prefix = input_string[:i]
            if prefix in dictionary:
                suffix = input_string[i:]
                suffix_segmentation = self.string_segments(suffix, dictionary)
                if suffix_segmentation:
                    self._memoize[input_string] = prefix + " " + suffix_segmentation
                    return prefix + " " + suffix_segmentation
        self._memoize[input_string] = False
        return False


# uncomment these lines to play around with it.

# with open("/usr/share/dict/words", "r") as word_file:
#     words = set(word.strip() for word in word_file)

# words = words - set(["q", "w", "r", "t", "y", "u", "o", "p",
#                      "s", "d", "f", "g", "h", "j", "k", "l",
#                      "z", "x", "c", "v", "b", "n", "m"])

# segment = StringSegment()
# print(segment.string_segments("catcatdogdotcat", words))
