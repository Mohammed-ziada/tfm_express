import frappe
import requests
import json
from frappe.model.document import Document
import time
def get_token1():
    url = "https://sandbox-customerapi.tfmex.com/api/v1/Token"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "username": "apitest2798",
        "password": "Z;,tW+-OMbOAr5q"
    }

    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()

    token = res.json().get("result", {}).get("token")
    if not token:
        raise Exception("Token not found in API response")

    return f"Bearer {token}"
def get_token2():
    cache = frappe.cache()
    cached_token = cache.get_value("tfm_token")
    token_timestamp = cache.get_value("tfm_token_timestamp")


    if cached_token and token_timestamp:
        now = time.time()
        if now - float(token_timestamp) < 6 * 60 * 60:
            return cached_token

    
    url = "https://sandbox-customerapi.tfmex.com/api/v1/Token"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "username": "apitest2798",
        "password": "Z;,tW+-OMbOAr5q"
    }

    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()

    token = res.json().get("result", {}).get("token")
    if not token:
        raise Exception("Token not found in API response")

    bearer_token = f"Bearer {token}"

    
    cache.set_value("tfm_token", bearer_token)
    cache.set_value("tfm_token_timestamp", str(time.time()))

    return bearer_token

def get_token():
    cache = frappe.cache()
    cached_token = cache.get_value("tfm_token")
    token_timestamp = cache.get_value("tfm_token_timestamp")

    
    if cached_token and token_timestamp:
        now = time.time()
        if now - float(token_timestamp) < 6 * 60 * 60:  
            frappe.msgprint("✅ Using cached token")
            print("✅ Using cached token")
            return cached_token

    
    url = "https://sandbox-customerapi.tfmex.com/api/v1/Token"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "username": "apitest2798",
        "password": "Z;,tW+-OMbOAr5q"
    }

    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()

    token = res.json().get("result", {}).get("token")
    if not token:
        raise Exception("Token not found in API response")

    bearer_token = f"Bearer {token}"

    
    cache.set_value("tfm_token", bearer_token)
    cache.set_value("tfm_token_timestamp", str(time.time()))

    frappe.msgprint("♻️ Fetching new token from API")
    print("♻️ New token fetched from API:", bearer_token)
    print("⏰ Time:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))

    return bearer_token
    

# @frappe.whitelist()
# def send_to_tfm1(doc ,total_weight,quantity , content):
    
#     sales_order = frappe.get_doc('Sales Order', doc)
#     if (sales_order.custom_shipped == True):
#          frappe.msgprint("Order is Already Shipped")
#          return;

#     tfm_api_url = "https://sandbox-customerapi.tfmex.com/api/v1/SkyBill/new"
#     tfm_api_token = get_token()


#     payload = {
#         "ShipperReferenceNo": doc,
#         "totalWeight": total_weight,
#         "totalVolumeWeight": 0.1, #--------
#         "consignee": sales_order.customer_name,
#         "consigneeAddress": sales_order.custom_address_line_1,
#         "consigneeCountry": sales_order.custom_country,
#         "consigneeCity": sales_order.custom_city,#sales_order.custom_city, # ---------
#         "consigneeArea": sales_order.custom_area,
#         "consigneeMobile": sales_order.custom_phone or "0000000000",
#         "pieces": quantity, #quantity 
#         "deliveryServiceCode": "PrePaid", #checkbox if COD or not
#         # "valueAmount": 10000,
#         "codCurrencyCode": "AED",
#         "content" : content, 
#         "shipperRemarks": "",
#         "handlingPack": True,
#         "handlingCold": False,
#         "handlingFragile": True,
#         "printMode": 1
#     }

#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": tfm_api_token
#     }

#     try:
#         res = requests.post(tfm_api_url, headers=headers, json=payload)
#         res.raise_for_status()
#         data = res.json()
#         frappe.db.set_value("Sales Order", doc, "custom_shipped", True )
#         awb_number = data['result'][0]['awb']  # Corrected to 'data' and extracting the AWB

#         # Print the success message with AWB
#         frappe.msgprint(f"Shipment created successfully. Tracking #: {awb_number}")

#         frappe.db.set_value("Sales Order", doc, "custom_awb", awb_number)
#         trackShipment(doc,awb_number)
#         return data

        
#     except requests.exceptions.HTTPError as http_err:
#         frappe.msgprint(f"HTTP error: {res.status_code} - {res.text}")
#     except requests.exceptions.RequestException as e:
#         frappe.msgprint(f"Request failed: {str(e)}")


@frappe.whitelist()
def send_to_tfm(doc, total_weight, quantity, content):
    sales_order = frappe.get_doc('Sales Order', doc)
    
    if sales_order.custom_shipped:
        return {
            "error": True,
            "message": "Order is already shipped"
        }

    tfm_api_url = "https://sandbox-customerapi.tfmex.com/api/v1/SkyBill/new"
    tfm_api_token = get_token()

    payload = {
        "ShipperReferenceNo": doc,
        "totalWeight": total_weight,
        "totalVolumeWeight": 0.1,
        "consignee": sales_order.customer_name,
        "consigneeAddress": sales_order.custom_address_line_1,
        "consigneeCountry": sales_order.custom_country,
        "consigneeCity": sales_order.custom_city,
        "consigneeArea": sales_order.custom_area,
        "consigneeMobile": sales_order.custom_phone or "0000000000",
        "pieces": quantity,
        "deliveryServiceCode": "PrePaid",
        "codCurrencyCode": "AED",
        "content": content,
        "shipperRemarks": "",
        "handlingPack": True,
        "handlingCold": False,
        "handlingFragile": True,
        "printMode": 1
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": tfm_api_token
    }

    try:
        res = requests.post(tfm_api_url, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()

        awb_number = data['result'][0]['awb']
        frappe.db.set_value("Sales Order", doc, "custom_shipped", True)
        frappe.db.set_value("Sales Order", doc, "custom_awb", awb_number)

        trackShipment(doc, awb_number,tfm_api_token)

        return data  # بيرجع الريسبونس كله
    except requests.exceptions.HTTPError as http_err:
        return {
            "error": True,
            "status_code": res.status_code,
            "error_text": res.text
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": True,
            "error_text": str(e)
        }
        


@frappe.whitelist()
def trackShipment(doc,awb ,tfm_api_token):
    
    sales_order = frappe.get_doc('Sales Order', doc)
    tfm_api_url = "https://sandbox-customerapi.tfmex.com/api/v1/SkyBill/trackbyawb"
   
    
    
    payload = {
         "awb": awb

    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": tfm_api_token
    }
    
    try:
        res = requests.post(tfm_api_url, headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        
        sub_status = data['result'][0]['subStatus']  
        futureDelivery = data['result'][0]['futureDeliveryDate']
        
        

        frappe.db.set_value("Sales Order", doc, "custom_shipment_status", sub_status)
        frappe.db.set_value("Sales Order", doc, "custom_future_date", futureDelivery)


        
    except requests.exceptions.HTTPError as http_err:
        frappe.msgprint(f"HTTP error: {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        frappe.msgprint(f"Request failed: {str(e)}")
        
        
        
        
        
        
        
@frappe.whitelist()
def trackShipmenthourly():
    sales_orders = frappe.get_all("Sales Order", fields=["name", "customer", "transaction_date"])

    for so in sales_orders:
        doc_Shipped = frappe.get_doc("Sales Order", so.name)
        if doc_Shipped.custom_shipped:
            trackShipment(so.name,doc_Shipped.custom_awb)
            
            doc_Shipped.reload()
            
            frappe.msgprint(f"changed : {so.name} {doc_Shipped.custom_awb} {doc_Shipped.custom_shipment_status}")
            # frappe.msgprint(f"changed : {so.name} {doc_Shipped.custom_awb} {doc_Shipped.custom_shipment_status} ")
    
    
        
