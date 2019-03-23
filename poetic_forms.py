''' produces poems with various structured forms, like sonnets '''
import argparse
from model import Model

def couplet(model):
    ''' two rhyming lines '''
    rh = None
    lines = []
    for _ in range(2):
        lines.append(model.get_line(rhyme_token=rh))
        if not lines[-1]:
            print('failed')
            return False
        rh = lines[0][0]
    return lines

def petrarchan(model):
    ''' a patrarchan sonnet '''
    try:
        lines = [model.get_line()]
        A = lines[0][0]
        lines.append(model.get_line())
        B = lines[-1][0]
        lines.append(model.get_line(rhyme_token=A))
        lines.append(model.get_line(rhyme_token=B))
        B = lines[-1][0]
        lines.append(model.get_line(rhyme_token=B))
        lines.append(model.get_line(rhyme_token=A))
        A = lines[0][0]
        lines.append(model.get_line())
        C = lines[-1][0]
        lines.append(model.get_line())
        D = lines[-1][0]
        lines.append(model.get_line())
        E = lines[-1][0]
        lines.append(model.get_line(rhyme_token=C))
        lines.append(model.get_line(rhyme_token=D))
        lines.append(model.get_line(rhyme_token=E))
    except TypeError:
        return False
    return lines

def print_poem(poem):
    ''' helper function to print a poem '''
    if not poem:
        print('Poem error')
        return

    for line in poem:
        try:
            print(' '.join(t['word'] for t in line[::-1]))
        except TypeError:
            print('Line error')
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', '-c')
    parser.add_argument('--model', '-m')
    args = parser.parse_args()
    if args.corpus:
        poet = Model(corpus_file=args.corpus)
        poet.save_model('corpus.model')
    elif args.model:
        poet = Model(model_file=args.model)

    #print_poem(couplet(poet))
    print_poem(petrarchan(poet))
    import pdb;pdb.set_trace()

