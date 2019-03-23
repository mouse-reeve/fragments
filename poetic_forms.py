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
    lines = [model.get_line()]
    A = lines[0][0]
    lines.append(model.get_line())
    B = lines[-1][0]
    lines.append(model.get_line(rhyme_token=A))
    lines.append(model.get_line(rhyme_token=B))
    lines.append(model.get_line(rhyme_token=B))
    lines.append(model.get_line(rhyme_token=A))
    lines.append(model.get_line())
    C = lines[-1][0]
    lines.append(model.get_line())
    D = lines[-1][0]
    lines.append(model.get_line())
    E = lines[-1][0]
    lines.append(model.get_line(rhyme_token=C))
    lines.append(model.get_line(rhyme_token=D))
    lines.append(model.get_line(rhyme_token=E))
    return lines


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

    poem = couplet(poet)#petrarchan(poet)
    if poem:
        for line in poem:
            print(' '.join(t['word'] for t in line[::-1]))
        for line in poem:
            print(' '.join(t['meter'] for t in line[::-1]))
    import pdb;pdb.set_trace()

