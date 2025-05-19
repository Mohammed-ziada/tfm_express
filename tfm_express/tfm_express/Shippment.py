import frappe
import requests
import json
from frappe.model.document import Document
import time
import base64
from frappe.utils.file_manager import save_file
def get_token():
    cache = frappe.cache()
    cached_token = cache.get_value("tfm_token")
    token_timestamp = cache.get_value("tfm_token_timestamp")

    
    if cached_token and token_timestamp:
        now = time.time()
        if now - float(token_timestamp) < 6 * 60 * 60:  
            # frappe.msgprint("✅ Using cached token")
            # print("✅ Using cached token")
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

    # frappe.msgprint("♻️ Fetching new token from API")
    # print("♻️ New token fetched from API:", bearer_token)
    # print("⏰ Time:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))

    return bearer_token
    



@frappe.whitelist()
def send_to_tfm(doc, total_weight, quantity, content ,name):
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
        "consignee": name,
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
        "printMode": 2
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
        awb_file = data['result'][0]['awbFile']
        frappe.db.set_value("Sales Order", doc, "custom_shipped", True)
        frappe.db.set_value("Sales Order", doc, "custom_awb", awb_number)
        frappe.db.set_value("Sales Order", doc, "custom_awb_files", awb_file)


        
        trackShipment(doc, awb_number,tfm_api_token)

        return data 
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
        frappe.db.set_value("Sales Order", doc, "custom_future_pickup_date", futureDelivery)


        
    except requests.exceptions.HTTPError as http_err:
        frappe.msgprint(f"HTTP error: {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        frappe.msgprint(f"Request failed: {str(e)}")
        
        
        
        
        
        
        
@frappe.whitelist()
def trackShipmenthourly():
    tfm_token = get_token()
    sales_orders = frappe.get_all("Sales Order", fields=["name", "customer", "transaction_date"])

    for so in sales_orders:
        doc_Shipped = frappe.get_doc("Sales Order", so.name)
        if doc_Shipped.custom_shipped:
            trackShipment(so.name,doc_Shipped.custom_awb ,tfm_token )
            
            doc_Shipped.reload()
            
            frappe.msgprint(f"changed : {so.name} {doc_Shipped.custom_awb} {doc_Shipped.custom_shipment_status}")
            frappe.msgprint(f"changed : {so.name} {doc_Shipped.custom_awb} {doc_Shipped.custom_shipment_status} ")
    
    
# @frappe.whitelist()
# def getPrintedBill(awb_file ,docname):
#     #get the base64 from the api
#     #enter it to this fnciton t decode it 
#     #after decode send this to Shippment to 
#     pdf_data = base64.b64decode(awb_file)
#     # pdf_data = base64.b64decode(awb_file)

  
#     file_name = f"awb_{docname}.pdf"

#     saved_file = save_file(file_name, pdf_data, "Sales Order", docname, is_private=1)

#     frappe.msgprint("success")
#     return {
#         "file_url": saved_file.file_url,
#         "file_name": saved_file.file_name
#     }