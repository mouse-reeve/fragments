''' read a corpus and create a markov model '''
import argparse
from collections import defaultdict
import json
import nltk
import re

cmudict = nltk.corpus.cmudict.dict()

class Token(object):
    ''' a lexical token with all its meta-information '''
    def __init__(self, word, phonemes):
        rhyme = get_rhyme_ending(phonemes)
        self.rhyme = rhyme
        self.phonemes = phonemes
        # CMUdict marks vowles with 0/1/2 for:
        # 0: unstressed, 1: stressed, 2: secondary stress
        self.meter = re.sub(r'\D', '', ''.join(phonemes))
        self.word = word


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

class Model(object):
    ''' the markov chain, rhyming dict, and tokenset created from the corpus '''
    tokens = []
    markov = defaultdict(list)
    rhymes = defaultdict(list)

    def __init__(self, corpus_file=None, model_file=None):
        if corpus_file:
            # assuming the file is a list of sentences and already sanitized
            for line in open(corpus_file, 'r'):
                self.parse(line)
        if model_file:
            # load a saved model file
            model = json.load(open(model_file, 'r'))
            self.tokens = model['tokens']
            self.markov = model['markov']
            self.rhymes = model['rhymes']


    def parse(self, text):
        ''' tokenize text and build a markov chain and rhyming dictionary '''
        prev = None
        for word in nltk.word_tokenize(text):
            # arguably I should try to preserve capitals in some cases (ie,
            # a location name) and not in others (the start of a sentence)
            word = word.lower()

            # TODO: this should guess the pronunciation instead, and handle punctuation
            if word not in cmudict:
                word = 'beep'

            # CMU gives us various alternate prounications of a word
            phonemeset = cmudict[word]
            for phonemes in phonemeset:
                token = Token(word, phonemes)
                self.tokens.append(token)
                self.rhymes[token.rhyme].append(token)
                # create the backwards markov reference, word two -> word one
                # backwards makes it easier to search based on terminal rhymes
                if prev:
                    self.markov[token.word].append(prev)
            prev = token

    def save_model(self, filename='trained.model'):
        ''' json dump the model into a file so we don't have to rebuild '''
        model_json = {
            'markov': self.markov,
            'rhymes': self.rhymes,
            'tokens': self.tokens,
        }
        json.dump(model_json, open(filename, 'w'), default=lambda x: x.__dict__)


    def get_line(self, start, meter=None, rhyme=None):
        ''' depth first search through the markov model given the meter and
        rhyme constraints '''
        return []

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', '-c', help='a text file from which to generate a model')
    parser.add_argument('--model', '-m', help='an existing model')
    args = parser.parse_args()
    if args.corpus:
        new_model = Model(corpus_file=args.corpus)
        new_model.save_model('corpus.model')
    elif args.model:
        old_model = Model(model_file=args.model)

