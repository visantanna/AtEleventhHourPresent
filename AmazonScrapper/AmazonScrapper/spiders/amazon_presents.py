import scrapy
import re
from entities.child_page import ChildPage
import logging

class AmazonPresentsSpider(scrapy.Spider):
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    name = 'amazon-presents'
    allowed_domains = ['amazon.com.br']
    start_urls = ['https://www.amazon.com.br/gcx/-/gfhz/api/scroll?canBeGiftWrapped=false&categoryId=adult-male&count=50&isLimitedTimeOffer=false&isPrime=false&offset=0&priceFrom&priceTo&searchBlob']
    offset_limit = 20


    def parse(self, response):
        json_convertible =True
        try:
            response.json()
        except: 
            json_convertible = False
        
        
        if json_convertible and 'asins' in response.json().keys():
            for next_page_to_process in self.main_page_processing(response):
                yield next_page_to_process

            
    def main_page_processing(self, response):
        productlist  = response.json()['asins']
        #returns the pages with the actual information
        for product_row in productlist:
            #Children page example
            #https://www.amazon.com.br/dp/B07DPYX7H6/ref=cm_gf_aAM_i10_d_p0_qd0_XAMQuzuahQYgFnuA61aw
            #Children page made from 3 components: 
            # default: https://www.amazon.com.br/dp/
            # asin: B07DPYX7H6
            # reftag: cm_gf_aAM_i10_d_p0_qd0_XAMQuzuahQYgFnuA61aw

            asin = product_row['asin']
            reftag =  product_row['reftag']
            image_url = product_row['displayLargeImageURL']

            default_url = "https://www.amazon.com.br/dp/{asin}/ref={reftag}"
            children_page_url = default_url.format(asin = asin , reftag= reftag)

            yield scrapy.Request(children_page_url, callback = self.child_page_processing , meta={'Image_url': image_url }) 
        

        #returns the next parent pages to process
        url=response.url
        
        
        regex = r'(?<=offset\=).*?(?=\&)'
        current_offset= int(re.findall(regex , url)[0])
        print("CURRENT_OFFSET:" + str(current_offset))
        current_offset = current_offset+1
        if current_offset <= self.offset_limit:
            yield scrapy.Request("https://www.amazon.com.br/gcx/-/gfhz/api/scroll?canBeGiftWrapped=false&categoryId=adult-male&count=50&isLimitedTimeOffer=false&isPrime=false&offset="+str(current_offset)+ "&priceFrom&priceTo&searchBlob" , callback = self.parse)    

    def child_page_processing(self, response):
        child_page = ChildPage(response.url , response.meta.get('Image_url') , response)
        if(child_page.failed == True):
            for error in child_page.error_list:
                logging.error( error)
        scrapped_item = {
            "product_name" : child_page.product_name,
            "url" : child_page.url,
            "url_image" : child_page.url_image,
            "price" : child_page.price,
            "early_delivery_date": child_page.early_delivery,
            "late_delivery_date":child_page.late_delivery
        }
        yield scrapped_item