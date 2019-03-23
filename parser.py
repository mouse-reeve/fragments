''' process a block of text '''
from collections import defaultdict
import nltk
import random
import re

cmudict = nltk.corpus.cmudict.dict()

class Token(object):
    ''' a lexical token (probably a word) with all its meta-information '''
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
    # if the word ends in a vowel soun, include the leading consonant
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

tokens = []
markov = defaultdict(list)
rhymes = defaultdict(list)
def parse(text):
    ''' tokenize text and build a markov chain and rhyming dictionary '''
    prev = None
    for word in nltk.word_tokenize(text):
        word = word.lower()
        if word not in cmudict:
            print('could not find "%s"' % word)
            word = 'beep'

        # CMU gives us various alternate prounications of a word
        phonemeset = cmudict[word]
        for ph in phonemeset:
            token = Token(word, ph)
            tokens.append(token)
            rhymes[token.rhyme].append(token)
            if prev:
                markov[token.word].append(prev)
                # this is how we'd do it if we were going start to end
                # instead of end to start:
                # markov[prev.word].append(token)
        prev = token

def get_prev_word(start, meter=None, max_syllables=None, rhyme=None):
    ''' find the next word given a series of constraints '''
    if not start:
        # so that I can start working from a random point
        options = tokens
    else:
        options = markov[start]
    valid = []
    for option in options:
        if (not meter or re.match(r'.*'+option.meter+'$', meter)) and \
           (not max_syllables or len(option.meter) <= max_syllables) and \
           check_rhyme(option, rhyme):
            valid.append(option)
    if not len(valid):
        return False
    return random.choice(valid)

def check_rhyme(option, rhyme):
    ''' check if a word is a valid rhyme with a given word '''
    if not rhyme:
        # we don't care about rhyme
        return True
    if option.word == rhyme.word:
        # you can't rhyme a word with itself
        return False
    if option.rhyme == rhyme.rhyme:
        # and they have to have the same rhyme ending
        return True
    return False

def get_line(foot='01', meter=5, rhyme=None):
    ''' write a line '''
    line_tokens = []
    length = len(foot) * meter
    meter_position = (foot * meter)
    cursor = None
    while True:
        cursor = get_prev_word(
            cursor.word if cursor else None,
            meter=meter_position,
            max_syllables=length,
            rhyme=rhyme)
        if not cursor:
            return False
        line_tokens.append(cursor)

        length -= len(cursor.meter)
        meter_position = meter_position[:-1 * len(cursor.meter)]
        rhyme = None
        if meter_position == '' or not length:
            break
    return line_tokens

def try_to_get_line(**kwargs):
    ''' retries get_line 20 times until it succeeds '''
    for _ in range(400):
        attempt = get_line(**kwargs)
        if attempt:
            return attempt
    return False

def couplet():
    rh = None
    lines = []
    for _ in range(2):
        lines.append(try_to_get_line(rhyme=rh))
        if not lines[-1]:
            print('failed')
            return False
        rh = lines[0][0]
    for line in lines:
        print(' '.join([t.word for t in line[::-1]]))
    for line in lines:
        print(' '.join([t.meter for t in line[::-1]]))
    return lines

def petrarchan():
    lines = [try_to_get_line()]
    A = lines[0][0]
    lines.append(try_to_get_line())
    B = lines[-1][0]
    lines.append(try_to_get_line(rhyme=A))
    lines.append(try_to_get_line(rhyme=B))
    lines.append(try_to_get_line(rhyme=B))
    lines.append(try_to_get_line(rhyme=A))
    lines.append(try_to_get_line())
    C = lines[-1][0]
    lines.append(try_to_get_line())
    D = lines[-1][0]
    lines.append(try_to_get_line())
    E = lines[-1][0]
    lines.append(try_to_get_line(rhyme=C))
    lines.append(try_to_get_line(rhyme=D))
    lines.append(try_to_get_line(rhyme=E))
    for line in lines:
        print(' '.join([t.word for t in line[::-1]]))
    for line in lines:
        print(' '.join([t.meter for t in line[::-1]]))
    return lines


if __name__ == '__main__':
    for line in open('corpus.txt', 'r'):
        parse(line)

    lines = couplet()


    import pdb;pdb.set_trace()

