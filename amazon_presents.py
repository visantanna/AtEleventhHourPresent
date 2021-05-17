import scrapy


class AmazonPresentsSpider(scrapy.Spider):
    name = 'amazon-presents'
    allowed_domains = ['https://www.amazon.com.br/gcx/Presentes-para-homens/gfhz/category?categoryId=adult-male']
    start_urls = ['http://www.amazon.com.br/gcx/Presentes-para-homens/gfhz/category?categoryId=adult-male/']

    def parse(self, response):
        product = response.xpath('//figure/div/a/@Title/text()')
        row_data = zip(product)

        
        for item in row_data:
            
            scrapped_info = {
                'product' : item[0]
            }
                
        yield scrapped_info
