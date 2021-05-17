from datetime import datetime
from dateutil.relativedelta import relativedelta
import locale
import logging 

class ChildPage():
    def __init__( self, url ,url_image , response):
        self.logger = logging.getLogger()
        self.url = url
        self.url_image = url_image
        self.failed = False
        self.error_list = []
        self.product_name = self.get_product_name_from_response(response)        
        self.price = self.get_price_from_response(response)        
        delivery_data = self.get_delivery_data_from_response(response)
        self.early_delivery = delivery_data['early']
        self.late_delivery = delivery_data['late']

    def get_product_name_from_response(self , response):
        product_list = response.css('#productTitle::text').extract()
        
        if self.error(product_list , "product name"):
            return ""
        else:
            return product_list[0].replace('\n' , '')
    
    def get_price_from_response(self, response):
        price_list = response.css('#price::text').extract()
        price_list.extend(response.css('#priceblock_ourprice::text').extract())
        price_list.extend(response.css('#price_inside_buybox::text').extract())
        new_list = []
        for price in price_list:
           processed_price = self.process_price_text(price)
           if processed_price != "":
               new_list.append(processed_price)
        price_list = new_list
        if self.error(price_list , "price"):
            return ""
        else:
            return price_list[0]

    def get_delivery_data_from_response(self , response):
        sorted_list_of_delivery = [
            '#mir-layout-DELIVERY_BLOCK-slot-UPSELL > b::text',
            '#mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_BADGE > b ::text',
            '#mir-layout-DELIVERY_BLOCK-slot-DELIVERY_MESSAGE > b::text',
            '#mir-layout-DELIVERY_BLOCK-slot-EXTENDED_DELIVERY_PROMISE_MESSAGE > b::text',
            '#mir-layout-DELIVERY_BLOCK-slot-HOLIDAY_DELIVERY_MESSAGE > b::text',
            '#mir-layout-DELIVERY_BLOCK-slot-SUPPLEMENTAL_DELIVERY_MESSAGE > b::text',
            '#mir-layout-DELIVERY_BLOCK-slot-CORE_FREE_SHIPPING_SUPPLEMENTARY_MESSAGE > b::text' 
        ]

        delivery_date_found = []
        for delivery_type in sorted_list_of_delivery:
            delivery_date_found = response.css(delivery_type).extract()
            if len(delivery_date_found) > 0 :
                break
        if self.error(delivery_date_found , "delivery date"):
            return {"early":"" , "late":""}
        else: 
            return self.process_delivery_text(delivery_date_found[0])

    def error(self , attr_list , attr_name):
        if len(attr_list) != 1:
            if len(attr_list) == 0:
                self.failed = True
                empty_attr_error = "No {attr} found".format(attr=attr_name)
                self.error_list.append(empty_attr_error)
                return True
            else: 
                more_than_one_warning = "more than one {attr} found: {attr_list}".format(attr= attr_name , attr_list = attr_list) 
                self.logger.warn(more_than_one_warning)
                
        return False

    def process_delivery_text(self , delivery_text):
        #Text formats:
        #   1 - 7 de Jun
        #   19 - 21 de Mai
        #   Terça-feira, 18 de Mai
        #   27 de Mai - 1 de Jun
        locale.setlocale(locale.LC_TIME ,"pt_BR.UTF-8" )
        week_days = [
            "Segunda-feira" ,
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo"
        ]
        
        for week_day in week_days:
            if week_day in delivery_text:
                delivery_text = delivery_text.replace(week_day , '')
                delivery_text = delivery_text.replace(',' , '')
        
        ##formating delivery_text 
        delivery_text = delivery_text.replace(' ' ,'').replace('\n' , '')
        dates = delivery_text.split("-")
        new_dates =[]
        for ddate in dates:
            new_dates.append(' '.join(ddate.split()))

        dates = new_dates

        #18 de Mai
        if len(dates) == 1:
            #assure that the day will be zero-padded
            delivery_date = self.get_date_from_day_month_text(dates[0])
            return { 'early': delivery_date , 'late':delivery_date}
        elif len(dates) == 2:
            #   27 de Mai - 1 de Jun
            #   1 de Mai - 7 de Jun
            if len(delivery_text) >= 12:
                early_delivery_date = self.get_date_from_day_month_text(dates[0])
                late_delivery_date = self.get_date_from_day_month_text(dates[1])
                return { 'early': early_delivery_date , 'late':late_delivery_date}
            
            #   1 - 7 de Jun
            #   19 - 21 de Mai
            else:
                dates[0] = dates[0] + dates[1][-5:]
                early_delivery_date = self.get_date_from_day_month_text(dates[0])
                late_delivery_date = self.get_date_from_day_month_text(dates[1])
                return { 'early': early_delivery_date , 'late':late_delivery_date}

    def get_date_from_day_month_text(self, delivery_date):
        if len(delivery_date) == 6:
                delivery_date = "0"+delivery_date
        dt_month_and_day = datetime.strptime(delivery_date,'%dde%b')
        #there is no year on the string so the year defaults to 1900
        #if the month and day of delivery is lower than the current means that the delivery date is in the next year
        year = 0
        current_date = datetime.now()
        dt_delivery_date = datetime(current_date.year , dt_month_and_day.month, dt_month_and_day.day)
        if current_date > dt_delivery_date: 
            dt_delivery_date = dt_delivery_date + relativedelta(years=1)

        str_formatted_delivery_date= dt_delivery_date.strftime("%Y%m%d")
        return str_formatted_delivery_date
        
    def process_price_text(self, price_string):
        return price_string.replace('\n', '').replace(' ','')