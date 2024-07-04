from nada_dsl import *

def nada_main():
    party1 = Party(name="Party1")
    party2 = Party(name="Party2")
    party3 = Party(name="Party3")
    a = SecretInteger(Input(name="A", party=party1))
    b = SecretInteger(Input(name="B", party=party2))

    
    result : list[SecretInteger] = [] 
    result.append(b)
    b= a%b
    result.append(b)

    outputs: list[Output] = []
    for i in range(2):
        outputs.append(Output(
            result[i],
            "result_" + str(i),
            party3
        ))
    return outputs