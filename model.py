''' read a corpus and create a markov model '''
import argparse
import json
import nltk
import random
import re

cmudict = nltk.corpus.cmudict.dict()

def get_rhyme_ending(phonemes):
    ''' grabs the ending phonemes of a word relevent to rhyme matching '''
    vowels = ['AA', 'AE', 'AH', 'AO', 'AW', 'AX', 'AXR', 'AY', 'EH', 'ER',
              'EY', 'IH', 'IX', 'IY', 'OW', 'OY', 'UH', 'UW', 'UX']
    rhyme = []
    # if the word ends in a vowel sound, include the leading consonant
    # if it ends in a consonant, do not
    # miasma doesn't rhyme with strata, pink does rhyme with link
    found_consonant = False
    found_vowel = False
    for phoneme in phonemes[::-1]:
        # ignore the cmu stress markers
        phoneme = re.sub(r'\d', '', phoneme)

        # we have a vowel and a consonant and the next sound is a consonant,
        # so we're done
        if found_consonant and found_vowel and phoneme not in vowels:
            break
        rhyme.append(phoneme)

        if phoneme in vowels:
            found_vowel = True
        else:
            found_consonant = True
    return ' '.join(rhyme[::-1])

def create_token(word, phonemes):
    ''' a lexical token with all its meta-information '''
    rhyme = get_rhyme_ending(phonemes)
    # CMUdict marks vowles with 0/1/2 for:
    # 0: unstressed, 1: stressed, 2: secondary stress
    meter = re.sub(r'\D', '', ''.join(phonemes))
    return {
        'word': word,
        'rhyme': rhyme,
        'meter': meter,
        'phonemes': phonemes,
        'syllables': len(meter),
    }

def create_weighted_choices(optionset):
    ''' now that we're done, let's make the structures easy to query
    what we start with:
      {fish: {'twenty': (<token>, 1), 'a': (<token>, 12), ...}, ...},
    what we want:
      {fish: {options: [<token>, <token>, ...], weights: [1, 12, ...], ...}
      '''
    clean = {}
    for (key, values) in optionset.items():
        unkeyed = values.values()
        options = [i[0] for i in unkeyed]
        weights = [i[1] for i in unkeyed]
        clean[key] = {'options': options, 'weights': weights}
    return clean

class Model(object):
    ''' the markov chain, rhyming dict, and tokenset created from the corpus '''
    tokens = {}
    markov = {}
    rhymes = {}

    def __init__(self, corpus_file=None, model_file=None):
        if corpus_file:
            # assuming the file is a list of sentences and already sanitized
            for line in open(corpus_file, 'r'):
                self.parse(line)

            # now that we're done, let's clean up the models
            # rhymes with only one entry won't work
            actual_rhymes = {}
            for rhyme in self.rhymes:
                if len(self.rhymes[rhyme]) > 1:
                    actual_options = [rhyme_clean(a) for a \
                            in self.rhymes[rhyme].keys()]
                    if len(set(actual_options)) > 1:
                        actual_rhymes[rhyme] = self.rhymes[rhyme]

            # change the structure so they can be queries
            self.markov = create_weighted_choices(self.markov)
            self.rhymes = create_weighted_choices(actual_rhymes)
            self.tokens = create_weighted_choices({'only': self.tokens})
            self.tokens = self.tokens['only']
        if model_file:
            # load a saved model file
            model = json.load(open(model_file, 'r'))
            self.tokens = model['tokens']
            self.markov = model['markov']
            self.rhymes = model['rhymes']


    def parse(self, text):
        ''' tokenize text and build a markov chain and rhyming dictionary '''
        prev = None
        # nltk.word_tokenize is too clever, it will break up "it's" into
        # ["it" "'s"] which is great for POS tagging but confuses things here
        for word in text.split(' '):
            # arguably I should try to preserve capitals in some cases (ie,
            # a location name) and not in others (the start of a sentence)
            word = word.lower()
            word = word.strip()
            sanitized = rhyme_clean(word)

            # punctuation
            if sanitized not in cmudict:
                if not re.match(r'\w', word):
                    # no letters -> skip it
                    continue

                # TODO: this should guess the pronunciation instead, and handle
                # it's an unknown word
                word = 'beep'
                sanitized = 'beep'

            # CMU gives us various alternate prounications of a word
            phonemeset = cmudict[sanitized]
            for phonemes in phonemeset:
                token = create_token(word, phonemes)
                self.add_token(token, prev=prev)
            prev = token


    def add_token(self, token, prev=None):
        ''' add the token to the various components of the model '''
        word = token['word']
        rhyme = token['rhyme']

        # increment token weights
        if word not in self.tokens:
            self.tokens[word] = [token, 0]
        self.tokens[word][1] += 1

        if rhyme not in self.rhymes:
            self.rhymes[rhyme] = {}
        if not word in self.rhymes[rhyme]:
            self.rhymes[rhyme][word] = [token, 0]
        self.rhymes[rhyme][word][1] += 1

        # create the backwards markov reference, word two -> word one
        # backwards makes it easier to search based on terminal rhymes
        if prev:
            # an entry looks like a dict of tokens and weights
            # 'fish': {'twenty': (<token>, 1), 'the': (<token>, 12), ...}

            if not word in self.markov:
                self.markov[word] = {}
            if prev['word'] not in self.markov[word]:
                self.markov[word][prev['word']] = [prev, 0]
            # increment the weight
            self.markov[word][prev['word']][1] += 1


    def save_model(self, filename='trained.model'):
        ''' json dump the model into a file so we don't have to rebuild '''
        model_json = {
            'markov': self.markov,
            'rhymes': self.rhymes,
            'tokens': self.tokens,
        }
        json.dump(model_json, open(filename, 'w'))


    def get_line(self, foot='01', meter=5, rhyme_token=None, rhymable=False):
        ''' depth first search through the markov model given the meter and
        rhyme constraints. The presets are iambic pentameter:
            foot='01' -> unstressed stressed (iamb),
            meter=5 -> 5 feet (pentameter)
        '''
        # this variable stores the meter for the unwritten part of the line,
        # so for iambic pentameter, it starts as 0101010101, and if we added
        # "life and death" to the end of the line, it would be 0101010
        meter_pattern = foot * meter

        line = self.get_next(meter_pattern, rhyme_token=rhyme_token,
                             rhymable=rhymable)
        return line

    def get_next(self, meter_pattern, line=None,
                 rhyme_token=None, rhymable=False):
        ''' try options recursively until one fits the constraints'''
        # happy ending conditions: the meter pattern is blank, ie used up
        if meter_pattern == '':
            return line

        line = line or []
        start = line[-1] if len(line) else None

        if start:
            # we have a starting word so use the markov chain, this is the most
            # common case. We use a weighted shuffle here.
            try:
                opts = self.markov[start['word']]
            except KeyError:
                # we just don't have a good next choice, sorry
                return False
        elif rhyme_token:
            # we have a rhyme so use the rhyming dictionary
            opts = self.rhymes[rhyme_token['rhyme']]
        else:
            # try 'em all
            opts = self.tokens

        # this shouldn't be set to true when there's a rhyme token or if it's
        # not the terminal word in the line
        if rhymable:
            okay = []
            # this is the case where the terminal word must have a workable
            # rhyme because the poet plans to make the next rhyme match it
            for (token, weight) in zip(opts['options'], opts['weights']):
                if token['rhyme'] in self.rhymes:
                    okay.append((token, weight))
            opts = {
                'options': [t[0] for t in okay],
                'weights': [t[1] for t in okay]
            }

        opts = weighted_shuffle(opts['options'], opts['weights'])

        opts = [t for t in opts \
                if suitable(t, meter_pattern, rhyme_token)]

        if not len(opts):
            # this start token isn't working, reject it
            return False

        # try each option until we find one that has children that work
        for option in opts:
            proposed_meter = meter_pattern[:-1 * option['syllables']]
            proposed_line = line + [option]
            # I'm not passing the rhyme token because it only matters to the
            # first word at the end of the line
            next_token = self.get_next(
                proposed_meter,
                line=proposed_line,
            )
            if isinstance(next_token, dict):
                line.append(next_token)
                break
            elif isinstance(next_token, list):
                # if we get a list (ie, a line), that means we succeeded
                return next_token
        return False


def suitable(option, meter_pattern, rhyme_token=None):
    ''' check if a word fits the meter and rhyme constraints '''
    return re.match(r'.*' + option['meter'] + '$', meter_pattern) and \
       check_rhyme(option, rhyme_token)


def weighted_choice(weights):
    ''' taken from:
    nicky.vanforeest.com/probability/weightedRandomShuffling/weighted.html '''
    rnd = random.random() * sum(weights)
    for i, w in enumerate(weights):
        rnd -= w
        if rnd < 0:
            return i

def weighted_shuffle(options, weights):
    ''' taken from:
    nicky.vanforeest.com/probability/weightedRandomShuffling/weighted.html '''
    weights = list(weights) # make a copy of weights
    if len(options) != len(weights):
        print("weighted_shuffle: Lenghts of lists don't match.")
        return

    r = [0]*len(options) # contains the random shuffle
    for i in range(len(options)):
        j = weighted_choice(weights)
        r[i] = options[j]
        weights[j] = 0
    return r

def rhyme_clean(word):
    ''' remove any funny business for checking pronunciation/rhyme '''
    return re.sub(r'\W', '', word)

def check_rhyme(option, rhyme):
    ''' check if a word is a valid rhyme with a given word '''
    if not rhyme:
        # we don't care about rhyme
        return True
    if rhyme_clean(option['word']) == rhyme_clean(rhyme['word']):
        # you can't rhyme a word with itself
        return False
    if option['rhyme'] == rhyme['rhyme']:
        # and they have to have the same rhyme ending
        return True
    return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', '-c', help='a corpus to generate the model')
    parser.add_argument('--model', '-m', help='an existing model')
    args = parser.parse_args()

    if args.corpus:
        poetry_model = Model(corpus_file=args.corpus)
        poetry_model.save_model('corpus.model')
    elif args.model:
        poetry_model = Model(model_file=args.model)

    print('model is ready')

    sample_line = poetry_model.get_line()
    if sample_line:
        print(' '.join(t['word'] for t in sample_line[::-1]))
        sample_rhyme = poetry_model.get_line(rhyme_token=sample_line[0])
        if sample_rhyme:
            print(' '.join(t['word'] for t in sample_rhyme[::-1]))
