import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from backend import provider
from backend.calculator.models import *


ORIGINS = ['*']
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

app.mount("/frontend/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

HARDWARE = {
    'randomx': [
        {'gear_id': 'cpu_1', 'make': 'AMD', 'model': '2600X', 'hashrate': 4, 'units': 'KH/s', 'power': 75},
        {'gear_id': 'cpu_2', 'make': 'Intel', 'model': 'i7 k200', 'hashrate': 9, 'units': 'KH/s', 'power': 135}
        ],
    'progpow': [
        {'gear_id': 'gpu_1', 'make': 'AMD', 'model': '5900X', 'hashrate':  10, 'units': 'MH/s', 'power': 175},
        {'gear_id': 'gpu_2', 'make': 'GF', 'model': 'RTX3090', 'hashrate':  52, 'units': 'MH/s', 'power': 375}
        ],
    'cuckoo': [
        {'gear_id': 'asic_1', 'make': 'iPollo', 'model': 'G1Mini', 'hashrate':  1.2, 'units': 'GH/s', 'power': 120},
        ]
    }


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):

    example_rig = {
        'algorithm': 'randomx',
        'hashrate': 4,
        'units': 'KH/s',
        'power': 75,
        }

    context = {"request": request, 'hardware': HARDWARE, 'example_rig': example_rig}
    return templates.TemplateResponse("home.html", context)


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    context = {
        "request": request,
        "embed_url": f"https://docs.google.com/document/d/e/2PACX-1vSlaSAoWAt2y3mdd3Lyd_EAk0DoC"
                     f"6bwIy0Cd0gyuxt-z2Ckfa3HLWxYI6UROsR5gTU5IeGrV6RsTKGT/pub?embedded=true",
        "doc_url": "https://docs.google.com/document/d/1PsdICF2CahVFyF-ctDkOQpYoPUdqAU7LIy8vFxb1aVo/edit?usp=sharing"
        }
    return templates.TemplateResponse("about.html", context)


class Hardware(BaseModel):
    gear_id: str = None
    algo: str = None


@app.post("/hardware")
async def hardware(hdw: Hardware):
    response = {}

    for gear in HARDWARE[hdw.algo]:
        response[f"{gear['make']} {gear['model']}"] = gear['gear_id']

    return response


@app.post("/hardware/get")
async def hardware(hdw: Hardware):
    for model in HARDWARE[hdw.algo]:
        if hdw.gear_id in model['gear_id']:
            return model
        else:
            continue


@app.post("/calculate")
async def calculate(parser: Parser):
    parser.parse()
    # print(parser)
    rig = Rig(**parser.dict(include={'hashrate', 'algorithm', 'power_consumption'}))
    currency = Currency(**provider.MarketData().get(parser.currency))
    blockchain = Blockchain(**provider.BlockchainData().get_last_block())

    calc = Calculator(rig=rig, blockchain=blockchain, currency=currency,
                      pool_fee=parser.pool_fee, energy_price=parser.energy_price)

    response = calc.get_report(as_dict=True)

    def round_assets(data: list) -> float:
        if 'epic' in data[0].lower():
            return round(float(data[1]), 5)
        else:
            return round(float(data[1]), 2)

    for key, value in response.items():
        try: value[1] = round_assets(value)
        except Exception: continue

    print(response)

    return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8054)