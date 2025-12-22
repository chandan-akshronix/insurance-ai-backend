def user_to_dict(u):
    return {
        "userId": getattr(u, 'id', None),
        "name": getattr(u, 'name', None),
        "email": getattr(u, 'email', None),
        "phone": getattr(u, 'phone', None),
        "address": getattr(u, 'address', None),
        "dateOfBirth": getattr(u, 'dateOfBirth', None),
        "gender": getattr(u, 'gender', None),
        "panCard": getattr(u, 'panCard', None),
        "aadhar": getattr(u, 'aadhar', None),
        "joinedDate": getattr(u, 'joinedDate', None),
        "kycStatus": getattr(u, 'kycStatus', None),
        "profileImage": getattr(u, 'profileImage', None),
    }


def product_to_dict(p):
    return {
        "productId": getattr(p, 'id', None),
        "category": getattr(p, 'category', None),
        "name": getattr(p, 'name', None),
        "description": getattr(p, 'description', None),
        "price": getattr(p, 'price', None),
    }


def policy_to_dict(p):
    return {
        "policyId": getattr(p, 'id', None),
        "userId": getattr(p, 'userId', None),
        "type": getattr(p, 'type', None),
        "planName": getattr(p, 'planName', None),
        "policyNumber": getattr(p, 'policyNumber', None),
        "coverage": getattr(p, 'coverage', None),
        "premium": getattr(p, 'premium', None),
        "tenure": getattr(p, 'tenure', None),
        "startDate": getattr(p, 'startDate', None),
        "expiryDate": getattr(p, 'expiryDate', None),
        "benefits": getattr(p, 'benefits', None),
        "nominee": getattr(p, 'nominee', None),
        "nomineeId": getattr(p, 'nomineeId', None),
        "policyDocument": getattr(p, 'policyDocument', None),
    }


def payment_to_dict(p):
    return {
        "paymentId": getattr(p, 'id', None),
        "userId": getattr(p, 'userId', None),
        "policyId": getattr(p, 'policyId', None),
        "amount": getattr(p, 'amount', None),
        "orderId": getattr(p, 'orderId', None),
        "paidDate": getattr(p, 'paidDate', None),
        "paymentMethod": getattr(p, 'paymentMethod', None),
        "status": getattr(p, 'status', None),
        "transactionId": getattr(p, 'transactionId', None),
        "returnUrl": getattr(p, 'returnUrl', None),
        "paymentUrl": getattr(p, 'paymentUrl', None),
    }


def quotation_to_dict(q):
    return {
        "quotationId": getattr(q, 'id', None),
        "category": getattr(q, 'category', None),
        "fullName": getattr(q, 'fullName', None),
        "email": getattr(q, 'email', None),
        "phone": getattr(q, 'phone', None),
    }


def notification_to_dict(n):
    return {
        "notificationId": getattr(n, 'id', None),
        "userId": getattr(n, 'userId', None),
        "message": getattr(n, 'message', None),
        "time": getattr(n, 'time', None),
        "type": getattr(n, 'type', None),
        "read": getattr(n, 'read', None),
        "policyId": getattr(n, 'policyId', None),
    }


def document_to_dict(d):
    return {
        "documentId": getattr(d, 'id', None),
        "userId": getattr(d, 'userId', None),
        "policyId": getattr(d, 'policyId', None),
        "documentType": getattr(d, 'documentType', None),
        "documentUrl": getattr(d, 'documentUrl', None),
        "uploadDate": getattr(d, 'uploadDate', None),
        "fileSize": getattr(d, 'fileSize', None),
    }


def contact_to_dict(c):
    return {
        "contactId": getattr(c, 'id', None),
        "fullName": getattr(c, 'fullName', None),
        "phone": getattr(c, 'phone', None),
        "email": getattr(c, 'email', None),
        "category": getattr(c, 'category', None),
        "message": getattr(c, 'message', None),
    }


def claim_to_dict(c):
    return {
        "claimId": getattr(c, 'id', None),
        "userId": getattr(c, 'userId', None),
        "policyId": getattr(c, 'policyId', None),
        "claimType": getattr(c, 'claimType', None),
        "amount": getattr(c, 'amount', None),
        "status": getattr(c, 'status', None),
    }


def nominee_to_dict(n):
    return {
        "nomineeId": getattr(n, 'id', None),
        "userId": getattr(n, 'userId', None),
        "policyId": getattr(n, 'policyId', None),
        "name": getattr(n, 'name', None),
        "relationship": getattr(n, 'relationship_type', None),
        "phone": getattr(n, 'phone', None),
        "email": getattr(n, 'email', None),
    }


def activity_to_dict(a):
    return {
        "activityId": getattr(a, 'id', None),
        "userId": getattr(a, 'userId', None),
        "type": getattr(a, 'type', None),
        "description": getattr(a, 'description', None),
        "time": getattr(a, 'time', None),
        "amount": getattr(a, 'amount', None),
    }
