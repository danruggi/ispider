# api.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import multiprocessing
import os
from pathlib import Path
import json
import time
import threading

from contextlib import asynccontextmanager

from ispider_core.ispider import ISpider
from ispider_core.config import Settings
from ispider_core.utils.logger import LoggerFactory


"""
Add domains

curl -X POST http://localhost:8000/spider/domains/add \
  -H "Content-Type: application/json" \
  -d '{
        "domains": [
           "vazquezconstructionservicesllc.com", "idahoveterinarysurgery.com", "vogelappraisal.net", "vogue-drycleaning.com", "whitepinebuildersinc.com", "whitepinemotel.com", "whitepine-outfitters.com", "eatdrinkwhiterabbit.com", "rayjwhiteproperties.com", "claudiawhittenglass.com", "wholebeingmassage.com", "mountainvalleyhealthcare.com", "we-silver-jewels.com", "wilburncustomshop.com", "wildbuffalomedia.com", "wildcactussalontf.com", "wildcow.org", "metalcraftidaho.com", "grwei.com", "williamsfruitranch.com", "williamsphc.com", "willowtreepreschool.org", "willowviewconsulting.com", "wilsonharris.com", "windsorsnursery.com", "winnscompost.com", "winstonwatercooler.com", "winterridgefoods.com", "winterspirit.com", "painters-boise.com", "woodfuneralhome.com", "woodinnovations-idaho.com", "woodriverbotanicals.com", "woodingtonvet.com", "woodshayandgrain.com", "woodswheatcroft.com", "cityofweston-id.org", "woodysoutdoorpower.com", "woodystowing.net", "massageatworldtree.com", "wwe-idaho.com", "worldcastanglers.com", "carpetcleaninginsandpoint.com", "xviii.com", "xylem.com", "y7consulting.com", "yacht-clubmccall.com", "affordableraingutter.net", "airbagmodulerepair.com", "avalosmf.com", "bairdssmallenginerepairs.com", "beaverdencreations.com", "goldenbeegardening.com", "bluelakesgoldandsilver.com", "idaho-backflow.com", "boiseballoonsandbouncers.net", "canyonconstructionservices.net", "chirhoprecision.com", "chickadeedance.com", "denosllc.com", "depotgrilltwinfalls.com", "freedomelectricid.com", "inlandtarpandcover.com", "littlechampscare.com", "livedincurls.com", "jewlvacations.com", "maggiemalsonphotography.com", "magicvalleypipeandsteel.com", "magicvalleysquardance.com", "nelsonsautomotive.net", "photographybyjonceemay.com", "prettiesartistry.com", "pictureperfectesthetics.com", "pottingshedcreations.com", "powerplantweb.com", "preciseprototypes.net", "priestrivertoolrepair.com", "printa.com", "loyaltishanksent.com", "getbeauty-gethealth.com", "getinsuranceleads.io", "pocatellopitstop.com", "mybigcommerce.com", "thewhitetulipsalon.com", "ynotadvertising.net", "yoursolution.net", "yourtechllc.com", "y-rstorage.com", "wefinanceidaho.com", "mikemcgowanracing.net", "fightingchanceidaho.com", "graciesandpoint.com", "downtownsandpoint.com", "cbdamericanshaman.com", "itmattersaesthetics.com", "mrappliance.com", "coopernorman.com", "adamsmongoliangrillandasianfusion.com", "accidaho.com", "amigoautoid.com", "bassettbuildingsupply.com", "bathandbodyworks.com", "batsxpress.com", "idahots.com", "creationsofachild.com", "creeksideinnbandb.com", "dacsq.com", "dancedepot.com", "diamondmodernmedia.com", "autorepairjerome.com", "idmtnatv.com", "theidahopioneer.com", "idahoprecuthomes.com", "diyhomeandgardentips.com", "lifelinerepairs.com", "lighthousetattooidaho.com", "longbridgebookkeeping.com", "christianiarestaurant.com", "milkcratecreate.com", "numaxxperformance.com", "cpsagu.com", "outlawpizzeria.com", "oxfordsuitesboise.com", "sandpoint.com", "sbtribes.com", "roeann.com", "roguemarketinganddesign.com", "rollinghcycles.com", "stromelectric.net", "ticketstubssportspub.com", "stuckiconstruction.com", "studio93pro.com", "sunsetmarts.com", "supersealtech.com", "superiordoorcoid.com", "superiorsweepingidaho.com", "surveyvitals.com", "topgaragedoorsidahofalls.com", "tnesvcs.com", "topshedidaho.com", "torrescarcareid.com", "mytriathlonjewelry.com", "tvdrivingschool.com", "treasurevalleypaints.com", "treasurevalleyraingutters.com", "troypreschool.com", "jimdofree.com", "trudyskitchenidahocity.com", "trulynolenboise.com", "truthps.com", "whateverittakespainting.com", "samtheconcreteman.com", "kitchenpowerpopups.com", "rooterman.com", "absolutservicesllc.com", "atlaswebdevelopmentpro.com", "autospringcorp.com", "thecasaanejo.com", "casanuevoleonid.com", "uhaul.com", "countrystorage.net", "countrysidecrafts.net", "digitallibations.com", "dirtworkservice.com", "fenixphotography.com", "fiestaguadalajara.com", "garyswindshields.com", "gatecitycollective.com", "gaylonsautobodyrepair.com", "idahomdesign.net", "idawild.info", "jbcbuilds.us", "higginssigns.net", "lonecypresswindowcleaning.com", "lonepinenursery.com", "millsangusbulls.com", "minaliocouturier.com", "massagebyrach.com", "mhsprings.com", "id.gov", "northidahoheating.com", "mountainviewbehavioralhealth.com", "nyhusevents.com", "obsidiandb.com", "piecingparadise.com", "thepinnaclegrp.com", "mydirectstay.com", "pioneermhp.com", "risesandpoint.com", "risingriverinc.com", "stangerangus.com", "callthemasters.com", "starinflatables.com", "angieslist.com", "tires2goidaho.com", "tlc-woodcrafts.com", "tlksourcing.com", "whitehorsehomeinspections.com", "reynoldschapel.com", "thewickedspud.com", "work-idaho.com", "thescrubcorner.com", "yogaforwellnesspro.com", "crashchampions.com", "extremeluxurytravel.com", "goldenbabeidaho.com", "grayhawkfarm.com", "matrixamplification.com", "omniss.com", "mrhandyman.com", "spencershandyman.com", "wedoitallhandyman.com", "reputationmarketingagency.net", "rovebackcountry.com", "visitsandpoint.com", "atdidahofalls.com", "lilylaceflowers.net", "boiseschools.org", "sunvalleyexpress.com", "supremelawncareservices.com", "briobowls.net", "coeurdalene-lawn-care.com", "klassypermanentcosmetics.com", "cdadoggrooming.com", "press-times.com", "alpinephysicaltherapyidaho.com", "8bitbarbershop.com", "afigym.com", "ajplace.top", "auroraspaunique.com", "autotrustboise.com", "portalced.com", "therivervalleyhandyman.com", "2ttrailers.com", "3heartoutfitters.net", "idahodj.com", "ascentwatersports.com", "babe-cave-beauty-bar.com", "boisewindowtint.com", "cafe95idaho.com", "chinakitchensandpoint.com", "infinityscreens.com", "crmframing.com", "countryautousedcars.com", "davesmithparts.com", "sonomafarmfresh.com", "desertbiotech.com", "dryridgeharriman.com", "toystoresunvalley.com", "eci-embroidery.com", "meligift.com", "europeanmobileautoworks.com", "fallcreekresortandmarina.com", "orderliliastacos.com", "gemstateprivateinvestigations.com", "harriswindows.net", "hauntedhollowpocatello.com", "heartwoodsandpoint.com", "helinamaries.com", "holidayfuture.com", "humeshandyman.com", "i84motorinn.com", "idahooutbackadventures.com", "impressedcoffeeco.com", "jcpitcrew.com", "kidz-connection.com", "lammcocpa.com", "lctreeservicellc.com", "ldasecurity.com", "shopsettings.com", "legendsboise.com", "libertyconstructionanddesigns.com", "lissaslearningladder.com", "thelowmaninn.com", "lowmanyurts.com", "lutherheights.org", "millersminiacres.com", "misterstandman.com", "moscowtreefarm.com", "usda.gov", "mountainviewservice.com", "nampahomeimprovement.com", "north-91.com", "northwestpizzacompany.com", "northwestplanthealthcare.com", "ohhoneybeestroandapiaries.com", "protrustwaterdamage.com", "landscapingsandpoint.com", "ozziesshoes.com", "usedcars-pocatello.com", "panteramarket2.com", "panteramarket.com", "patriciamariecrafts.com", "pingman.com", "platosclosetboise.com", "poweraudiovideo.com", "priestlaketech.com", "professionalframeandgallery.com", "professionalpumpservices.com", "profitsrn.com", "profotofix.com", "radcurbside.com", "rigginsrodeo.com", "polsontheatres.com", "visitrootshair.com", "rootslandcrew.com", "rolfsandpoint.com", "sarah-jacobson.com", "severnwinkle.com", "silverautollc.com", "silverbridgecpas.com", "slidingsaussies.com", "slimchickens.com", "truckandautoworks.com", "stjoeriverhideaway.com", "sterlinglewiston.com", "cdajewelry.com", "sunvalleyart.com", "svanimal.com", "sunvalleyfabric.com", "sunvalleygardencenter.com", "sunvalleygifts.com", "cornercafepf.com", "thecosmeticheart.com", "thejewelrybar-sandpoint.com", "thejumparoundidaho.com", "theprofitgameplan.com", "theshopgrooming.com", "shredderboise.com", "thevillagebakerycda.com", "thorcocda.com", "nativeseedfarm.com", "idahorenaissancefaire.com", "thorntonheatingandsheetmetal.com", "thorogold.com", "unionmarket.com", "untappedhealth.com", "upfab.co", "upnorthdistillery.com", "upthecreekhvac.com", "upgradeexcavation.com", "upliftskinboutique.com", "upliftstrengthandfitness.com", "upliftedgym.com", "uppervalleyvet.com", "urbantalent.com", "uscombustion.com", "usatuff.com", "utaraidaho.com", "walltentshop.com", "weldonfarms.com", "westonelogistics.com", "shopced.com", "basecampaviation.com", "bearriverrifleman.com", "clheilman.com", "camillebeckman.com", "cedardayspasandpoint.com", "comptonwoodcraft.com", "dykman.com", "ejkidsthetoystore.com", "festivalatsandpoint.com", "floorshowsandpoint.com", "flowersroxannebohman.com"
        ]
      }'


curl http://localhost:8000/spider/status

"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    global spider_instance, spider_config, spider_status, start_time

    config = SpiderConfig(
        domains=[],
        stage="unified",
        user_folder="/Volumes/Sandisk2TB/test_business_scraper_22"
    )
    spider_config = config
    spider_instance = ISpider(domains=config.domains, stage=config.stage, **config.model_dump(exclude={"domains", "stage"}))
    spider_status = "initialized"
    start_time = time.time()

    def run_in_background():
        run_spider()

    threading.Thread(target=run_in_background, daemon=True).start()

    yield  # App is running

    # (Optional) Cleanup logic can go here


app = FastAPI(title="ISpider API", 
              description="API for controlling the ISpider web crawler",
              version="0.1.0",
              lifespan=lifespan
              )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global state for active spiders
spider_instance = None
spider_config = None
spider_status = "not_started"
start_time = None

class SpiderConfig(BaseModel):
    domains: List[str] = []
    stage: Optional[str] = None
    user_folder: str = "/Volumes/Sandisk2TB/test_business_scraper_22"
    log_level: str = "DEBUG"
    pools: int = 4
    async_block_size: int = 4
    maximum_retries: int = 2
    codes_to_retry: List[int] = [430, 503, 500, 429]
    engines: List[str] = ["httpx", "curl"]
    crawl_methods: List[str] = ["robots", "sitemaps"]
    max_pages_per_domain: int = 5000
    websites_max_depth: int = 2
    sitemaps_max_depth: int = 2
    timeout: int = 5

class DomainAddRequest(BaseModel):
    domains: List[str]



@app.post("/spider/domains/add")
async def add_domains(request: DomainAddRequest):
    global spider_instance  # assuming you have a single global spider instance

    if not spider_instance:
        raise HTTPException(status_code=500, detail="Spider not initialized")

    new_domains = request.domains
    shared_new_domains = spider_instance.shared_new_domains

    if shared_new_domains is None:
        raise HTTPException(status_code=500, detail="Spider does not support dynamic domain addition")

    shared_new_domains.extend(new_domains)

    return {"message": "Domains added successfully", "added_domains": new_domains}



@app.get("/spider/status")
async def get_status():
    global spider_instance

    dom_stats = spider_instance.shared_dom_stats
    if dom_stats is None:
        raise HTTPException(status_code=500, detail="Domain stats not available")

    running_time = time.time() - start_time if start_time else 0

    with dom_stats.lock:
        status = {}
        for dom in dom_stats.dom_missing.keys():
            status[dom] = {
                "bytes": dom_stats.local_stats[dom].get('bytes', 0),
                "missing": dom_stats.dom_missing[dom],
                "total": dom_stats.dom_total[dom],
                "last_call": dom_stats.dom_last_call.get(dom, 0),
                "engine": dom_stats.dom_engine.get(dom)
            }

    return status


@app.post("/spider/stop")
async def stop_spider():
    global spider_status
    spider_status = "stopping"
    return {"message": "Stop signal sent (graceful shutdown not yet implemented)"}


def run_spider():
    global spider_instance, spider_status

    try:
        spider_status = "running"
        spider_instance._ensure_manager()
        spider_instance.run()
        spider_status = "completed"
    except Exception as e:
        spider_status = "failed"
        print(f"[ERROR] Spider failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)