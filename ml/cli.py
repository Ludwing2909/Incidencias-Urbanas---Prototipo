import argparse
import json
from pathlib import Path
from ml.data import validate, split_data, prepare, agreement
from ml.experiment import train, choose_threshold, evaluate, activate
from ml.inference import Predictor

def main():
    parser=argparse.ArgumentParser(description='Datos → particiones → entrenamiento → calibración → umbral → evaluación → activación')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('validate','agreement'):
        p=sub.add_parser(name); p.add_argument('source')
    for name in ('split','prepare'):
        p=sub.add_parser(name); p.add_argument('source'); p.add_argument('output')
    p=sub.add_parser('train'); p.add_argument('source'); p.add_argument('output'); p.add_argument('--seed',type=int,default=42); p.add_argument('--mode',choices=['real','hybrid'],default='hybrid'); p.add_argument('--demo',action='store_true')
    p.add_argument('--expanded',action='store_true',help='Comparación offline acotada de palabras/caracteres, LinearSVC y SVC de kernel, LR y NB')
    for name in ('threshold','evaluate'):
        p=sub.add_parser(name); p.add_argument('source'); p.add_argument('run')
        if name=='evaluate':
            p.add_argument('--partition',choices=['test','challenge','functional'],default='test')
            p.add_argument('--rules',default='config/demo_rules.json')
            p.add_argument('--destination-reference')
    p=sub.add_parser('activate'); p.add_argument('run'); p.add_argument('--target',default='models')
    p=sub.add_parser('predict'); p.add_argument('text'); p.add_argument('--manifest',default='models/active.json')
    args=parser.parse_args()
    try:
        if args.command=='validate':
            frame=validate(args.source); result={'rows':len(frame),'counts':frame.categoria.value_counts().to_dict(),'valid':True}
        elif args.command=='agreement': result=agreement(args.source)
        elif args.command=='split': result=split_data(args.source,args.output)
        elif args.command=='prepare': result=prepare(args.source,args.output)
        elif args.command=='train': result=train(args.source,args.output,args.seed,args.mode,args.demo,args.expanded)
        elif args.command=='threshold': result=choose_threshold(args.source,args.run)
        elif args.command=='evaluate': result=evaluate(args.source,args.run,args.partition,args.rules,args.destination_reference)
        elif args.command=='activate': result=activate(args.run,args.target)
        else:
            predictor=Predictor(args.manifest); topic,score,kind=predictor.predict(args.text)
            result={'tema':topic,'puntuacion':score,'tipo_puntuacion':kind,'error':predictor.error}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except ValueError as error:
        parser.exit(2,str(error)+'\n')

if __name__=='__main__': main()
