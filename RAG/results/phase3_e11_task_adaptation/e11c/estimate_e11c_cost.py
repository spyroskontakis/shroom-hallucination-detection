"""Offline heuristic token/cost estimate; never downloads a tokenizer or calls API."""
import math
import sys
from e11c_common import *


def main():
    spec=load_protocol()
    requests=read_rows(PRIVATE/'round_1/requests.jsonl')
    require(len(requests)==12000,'request count')
    # No verified tokenizer for this exact API model is available offline.
    # Include serialized schema and 32 tokens/request for framing as an estimate.
    sizes=[]
    for req in requests:
        body=req['body']
        text=body['instructions']+body['input'][0]['content']+encoded(body['text']['format']).decode()
        sizes.append((len(text),len(text.encode())))
    mid=sum(math.ceil(chars/4)+32 for chars,_ in sizes)
    lower=sum(math.ceil(chars/5)+32 for chars,_ in sizes)
    upper=sum(math.ceil(chars/3)+32 for chars,_ in sizes)
    byte_proxy=sum(byte_count+128 for _,byte_count in sizes)
    pricing=spec['pricing']
    def cost(input_tokens,output_tokens):
        standard=(input_tokens*pricing['standard_input_per_million']+
                  output_tokens*pricing['standard_output_per_million'])/1e6
        return {'standard_usd':round(standard,4),'batch_usd':round(standard*0.5,4)}
    report={'status':'ESTIMATE_NOT_API_TOKEN_COUNT','requests':12000,
            'method':'chars/4 + 32/request for prompt, serialized user JSON and schema; sensitivity chars/5..chars/3; not calibrated to exact model tokenizer',
            'estimated_input_tokens':mid,'input_sensitivity_range':[lower,upper],
            'conservative_input_byte_proxy':byte_proxy,
            'output_tokens_per_request_ceiling':2048,
            'first_pass_output_token_ceiling':12000*2048,
            'output_ceiling_includes_hidden_reasoning':True,
            'output_scenarios':{str(n):{'output_tokens':12000*n,**cost(mid,12000*n)}
                                for n in (256,512,1024,2048)},
            'first_pass_cost_at_output_ceiling':cost(mid,12000*2048),
            'three_attempts_cost_at_output_ceiling':cost(3*mid,3*12000*2048),
            'conservative_byte_proxy_cost_at_output_ceiling':cost(byte_proxy,12000*2048),
            'note':'Output use is unknown before labeling; no yield/average-output guarantee. No prompt caching discount, taxes or regional uplift assumed. Byte proxy is a planning allowance, not a proven model-specific bound.',
            'pricing':pricing,'python':sys.version.split()[0]}
    save(HERE/'E11C_COST_ESTIMATE.json',report)
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    main()
