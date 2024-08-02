RETRIEVE_CI_INFO_BY_KEY_RESPONSE = """{
        "Key": [
            "ID0042"
        ],
        "RequestType": "CI",
        "Source": "SERVICE-NOW CLOUD (P)",
        "information": [
            {
                "AicClassification": "322",
                "AuditStatus": "Audited",
                "BusinessOwner": "james.brown@archisure.eu",
                "BusinessOwnerDepartment": "BUSINESS AREA SVC NOW (_9876_)",
                "CiID": "ID0042",
                "CiName": "SERVICE-NOW CLOUD (P)",
                "CiSubtype": "Something on Azure",
                "CiType": "application",
                "ConfigAdminGroup": "ORG UNIT THE EAGLES",
                "ContactType": "Contact",
                "CreatedDate": "2022-03-30T13:35:52+00:00",
                "Description": [
                    "SERVICE-NOW enables organizations in all industries to easily automate and administer service requests.",
                    "ArchiSure SERVICE-NOW is being used for multiple processes."
                ],
                "EnableIncidentCreation": true,
                "Environment": [
                    "Production"
                ],
                "ExternalCI": true,
                "IAMProvisioningMethod": [
                    "OAuth 2.0"
                ],
                "PrimaryContact": "don_t.call.us.we.call.you@archisure.eu",
                "RelatedServiceComponent": "GREAT SERVICE FOR EVERYONE",
                "Status": "4Real",
                "SystemOwner": "chuck.norris@archisure.eu",
                "SystemOwnerDepartment": "DETECTION (_1234_)",
                "Title": "SERVICE NOW CLOUD",
                "Vendor": "Service Now"
            }
        ]
    }
"""

RETRIEVE_CI_BY_AUTHORIZATION_RESPONSE = """{
        "Key": [
            "chuck.norris@archisure.eu"
        ],
        "More": 0,
        "Source": "SERVICE-NOW CLOUD (P)",
        "TotalRecords": 9,
        "Type": "user",
        "information": [
            {
                "CIName": [
                    "TEAM1.CLOUD_(04-09-2023 10:06:41) (ID0012)",
                    "TEAM1.CLOUD_(04-09-2023 10:01:01) (ID0013)",
                    "TEAM1.CLOUD_(04-09-2023 10:06:40) (ID0014)",
                    "TEAM1.CLOUD_(04-09-2023 10:06:59) (ID0015)",
                    "INFORMATION_FACTORY_1 (ID0016)",
                    "DATAPOINT_ENGINE(ID0017)",
                    "SERVICE-NOW CLOUD (D) (ID0018)",
                    "SERVICE-NOW CLOUD (P) (ID0042)",                    
                    "SERVICE-NOW SUPPORT SERVICES - BATCH ORCHESTRATION [P] (ID0019)"                    
                ]
            }
        ]
    }"""

RETRIEVE_CI_RELATION_SHIPS_RESPONSE = """{
    "Key": ["SERVICE-NOW CLOUD (P)"],
    "Source": "SERVICE-NOW CLOUD (P)",
    "downstreamCIs": [{
            "DownstreamCIID": "ID0001",
            "DownstreamCIName": "EDL-SERVICE-NOW-CLOUD-PROD",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Something on Azure",
            "DownstreamCIType": "subapplication",
            "DownstreamCMSSource": "TERMINUS IN THE CLOUD",
            "DownstreamConfigAdmin": "EET T4FEC CDD RNL DT SERVICE-NOW",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "service.now@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "consumes"
        }, {
            "DownstreamCIID": "ID0002",
            "DownstreamCIName": "TERMINUS",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Nexus Repository",
            "DownstreamCIType": "applicationresource",
            "DownstreamCMSSource": "TERMINUS IN THE CLOUD",
            "DownstreamConfigAdmin": "ORG UNIT CODESCANNING AND REPOSITORY MANAGEMENT",
            "DownstreamDepartment": "ORG UNIT KEEPING IT NICE AND TIDY",
            "DownstreamFunctionalEmail": "nice.and.tidy@archisure.eu",
            "DownstreamManagerEmail": "david.carradine@archisure.eu",
            "DownstreamManagerName": "CARRADINE, DAVID",
            "DownstreamRelationshipSubtype": "consumes"
        }, {
            "DownstreamCIID": "ID0003",
            "DownstreamCIName": "SERVICE-NOW (P) ACP",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Some Web Thing",
            "DownstreamCIType": "subapplication",
            "DownstreamConfigAdmin": "ORG UNIT SERVICE-NOW 4REAL",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "service.now@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "Usage"
        }, {
            "DownstreamCIID": "ID0004",
            "DownstreamCIName": "SERVICE-NOW (P) ADP",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Some Web Thing",
            "DownstreamCIType": "subapplication",
            "DownstreamConfigAdmin": "ORG UNIT SERVICE-NOW 4REAL",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "service.now@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "Usage"
        }, {
            "DownstreamCIID": "ID0005",
            "DownstreamCIName": "SERVICE-NOW (P) CDD",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Some Web Thing",
            "DownstreamCIType": "subapplication",
            "DownstreamConfigAdmin": "ORG UNIT SERVICE-NOW 4REAL",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "service.now@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "Usage"
        }, {
            "DownstreamCIID": "ID0006",
            "DownstreamCIName": "SERVICE-NOW (P) CDD BATCH",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Batch Application",
            "DownstreamCIType": "subapplication",
            "DownstreamConfigAdmin": "ORG UNIT SERVICE-NOW 4REAL",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "service.now@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "Usage"
        }, {
            "DownstreamCIID": "ID0007",
            "DownstreamCIName": "SERVICE-NOW (P) CRS-FATCA",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Some Web Thing",
            "DownstreamCIType": "subapplication",
            "DownstreamConfigAdmin": "ORG UNIT THE EAGLES",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "the.eagles@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "Usage"
        }, {
            "DownstreamCIID": "ID0008",
            "DownstreamCIName": "SERVICE-NOW (P) CRS-FATCA BATCH",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Batch Application",
            "DownstreamCIType": "subapplication",
            "DownstreamConfigAdmin": "ORG UNIT THE EAGLES",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "the.eagles@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "Usage"
        }, {
            "DownstreamCIID": "ID0009",
            "DownstreamCIName": "SERVICE-NOW (P) EZO",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Some Web Thing",
            "DownstreamCIType": "subapplication",
            "DownstreamConfigAdmin": "ORG UNIT SERVICE-NOW 4REAL",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "service.now@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "Usage"
        }, {
            "DownstreamCIID": "ID0010",
            "DownstreamCIName": "SERVICE-NOW (P) WWFT BATCH",
            "DownstreamCIStatus": "4Real",
            "DownstreamCISubtype": "Batch Application",
            "DownstreamCIType": "subapplication",
            "DownstreamConfigAdmin": "ORG UNIT SERVICE-NOW 4REAL",
            "DownstreamDepartment": "DETECTION (_1234_)",
            "DownstreamFunctionalEmail": "service.now@archisure.eu",
            "DownstreamManagerEmail": "chuck.norris@archisure.eu",
            "DownstreamManagerName": "NORRIS, CHUCK",
            "DownstreamRelationshipSubtype": "Usage"
        }
    ],
    "upstreamCIs": [
            {
                "UpstreamCIID": "ID0042",
                "UpstreamCIName": "SERVICE-NOW CLOUD (P)",
                "UpstreamCIStatus": "4Real",
                "UpstreamCISubtype": "Something on Azure",
                "UpstreamCIType": "application",
                "UpstreamConfigAdmin": "ORG UNIT THE EAGLES",
                "UpstreamDepartment": "DETECTION (_1234_)",
                "UpstreamFunctionalEmail": "the.eagles@archisure.eu",
                "UpstreamManagerEmail": "chuck.norris@archisure.eu",
                "UpstreamManagerName": "NORRIS, CHUCK",
                "UpstreamRelationshipSubtype": "Usage"
            }
        ]
}
"""