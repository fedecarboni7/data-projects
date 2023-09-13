import website_scanner.spiders.booleanSpider.booleanSpider as booleanSpider
import website_scanner.spiders.linkedinSpider.linkedinSpider as linkedinSpider
import website_scanner.spiders.businessEntitySpider.businessEntitySpider as businessEntitySpider
import website_scanner.spiders.fddGatheringSpider.fddGatheringSpider as fddGatheringSpider
import website_scanner.spiders.companiesForSaleSpider.companiesForSaleSpider as companiesForSaleSpider
import website_scanner.spiders.e2VisaElegibilitySpider.e2VisaElegibilitySpider as e2VisaElegibilitySpider
import website_scanner.spiders.fbaSpiders.fbaInfoSpider.fbaInfoSpider as fbaInfoSpider
import website_scanner.spiders.fbaSpiders.fbaMembersSpider.fbaMembersSpider as fbaMembersSpider
import website_scanner.spiders.fbaSpiders.fbaAllMembersInfoSpider.fbaAllMembersInfoSpider as fbaAllMembersInfoSpider
import website_scanner.spiders.franchisetimesSpider.franchisetimesSpider as franchisetimesSpider
import website_scanner.spiders.restaurantbusinessonlineSpider.restaurantbusinessonlineSpider as restaurantbusinessonlineSpider
import website_scanner.spiders.entrepreneurSpider.entrepreneurSpider as entrepreneurSpider
import website_scanner.spiders.sbaSpider.sbaSpider as sbaSpider
import website_scanner.spiders.performanceSpider.performanceSpider as performanceSpider
import website_scanner.spiders.googleSpider.googleSpider as googleSpider
import website_scanner.spiders.chainStoreGuideSpider.chainStoreGuideSpider as chainStoreGuideSpider
import website_scanner.spiders.sbaFileGatheringSpider.sbaFileGatheringSpider as sbaFileGatheringSpider

from .utils import launch_spider

def dispatcher(context):

    if 'boolean_spider' in context['env']:
        launch_spider(booleanSpider, context)
        
    if 'linkedin_spider' in context['env']:
        launch_spider(linkedinSpider, context)

    if 'businessEntity_spider' in context['env']:
        launch_spider(businessEntitySpider, context)
    
    if 'fddGathering_spider' in context['env']:
        launch_spider(fddGatheringSpider, context)

    if 'companiesForSale_spider' in context['env']:
        launch_spider(companiesForSaleSpider, context)

    if 'e2VisaElegibility_spider' in context['env']:
        launch_spider(e2VisaElegibilitySpider, context)
    
    if 'fba_info_spider' in context['env']:
        launch_spider(fbaInfoSpider, context)

    if 'fba_members_spider' in context['env']:
        launch_spider(fbaMembersSpider, context)

    if 'fba_all_members_info_spider' in context['env']:
        launch_spider(fbaAllMembersInfoSpider, context)

    if 'franchisetimes_spider' in context['env']:
        launch_spider(franchisetimesSpider, context)

    if 'restaurantbusinessonline_spider' in context['env']:
        launch_spider(restaurantbusinessonlineSpider, context)

    if 'entrepreneur_spider' in context['env']:
        launch_spider(entrepreneurSpider , context)

    if 'sba_spider' in context['env']:
        launch_spider(sbaSpider , context)

    if 'performance_spider' in context['env']:
        launch_spider(performanceSpider , context)

    if 'google_spider' in context['env']:
        launch_spider(googleSpider , context)

    if 'chainStoreGuide_spider' in context['env']:
        launch_spider(chainStoreGuideSpider , context)

    if 'sbaGatheringSpider_spider' in context['env']:
        launch_spider(sbaFileGatheringSpider , context)