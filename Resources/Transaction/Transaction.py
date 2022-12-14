from datetime import datetime

from flask_restful import Resource
from Resources.External.HttpClient import HttpClient
from Models.ItemModels import ItemModel
from Models.StoreModels import StoreModel
from db import mongo
from Security.Args import transactionParser, creditScoreParser, transactionQueryParser


class Transaction(Resource):

    def post(self):

        try:
            response_data = transactionParser.parse_args()
            item = ItemModel.get_Item_By_Id(response_data['itemId'])
            if not item:
                return {'message': 'Selected Item not in store'}, 400  # Bad request

            store = StoreModel.get_Store_By_Id(item.store_id)

            transaction = {'business_id': store.business_id,
                           'store_id': store.id, 'amount': item.price, 'date': str(datetime.now().date()),
                           'status': 'completed'}
            transactionMongo = mongo.db.Transaction
            result = transactionMongo.insert_one(transaction)

            # Government tax authority api call
            data = {"order_id": result.inserted_id, "platform_code": "022", "order_amount": item.price}
            HttpClient.fire_and_forget(data)
            if result:
                return {'message': 'Transaction created successfully'}, 201  # Created
            return {'message': 'Transaction not created successfully'}, 500  # Server Error
        except Exception as e:
            return {'message': str(e)}, 500  # Server Error


class TransactionList(Resource):
    def get(self):
        try:
            transactionMongo = mongo.db.Transaction
            transactions = list(transactionMongo.find())

            # explicit is better than implicit, readability counts
            result = [{'business_id': transaction['business_id'], 'store_id': transaction['store_id'],
                       'amount': transaction['amount'], 'date': str(transaction['date']),
                       'status': transaction['status']}
                      for transaction in transactions]

            return result
        except Exception as e:
            return {'message': str(e)}, 500  # Server Error


class CreditScore(Resource):

    def post(self):
        response_data = creditScoreParser.parse_args()
        transactionMongo = mongo.db.Transaction

        # explicit is better than implicit, readability counts
        result = transactionMongo.find({"business_id": response_data['business_id']})
        transaction = list(result)
        total = sum(float(t['amount']) for t in transaction)

        answer = total / (len(transaction) * 100)

        return {'creditScore': answer}


class TransactionNumberTotal(Resource):

    def post(self):
        response_data = transactionQueryParser.parse_args()
        transactionMongo = mongo.db.Transaction

        # explicit is better than implicit, readability counts
        if response_data['today']:
            result = transactionMongo.find({"business_id": response_data['business_id'], "date":
                str(datetime.now().date())})

            return {'Total Number of Transaction Today': len(list(result))}

        result = transactionMongo.find({"business_id": response_data['business_id']})

        return {'Total Number of Transaction': len(list(result))}


class TotalTransactionAmount(Resource):

    def post(self):
        response_data = transactionQueryParser.parse_args()
        transactionMongo = mongo.db.Transaction

        # explicit is better than implicit, readability counts
        if response_data['today']:
            result = transactionMongo.find({"business_id": response_data['business_id'], "date":
                str(datetime.now().date())})
            total = sum(float(t['amount']) for t in result)
            return {'Total Amount of Transaction Today': total}

        result = transactionMongo.find({"business_id": response_data['business_id']})
        total = sum(float(t['amount']) for t in result)

        return {'Total Amount of Transaction': total}
