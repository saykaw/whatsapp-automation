const express = require('express')
const bodyparser = require('body-parser')
const axios = require('axios')
const moment = require('moment')
require('dotenv').config()

const app = express().use(bodyparser.json())

const token = process.env.TOKEN //sending the request
const mytoken = process.env.MYTOKEN //verifying the webhook
const flaskRAGUrl = process.env.FLASK_URL //flask server URL
const flaskDBUrl = process.env.FLASK_DB_URL;

app.listen(8000, () => {
    console.log('webhook is listening on port 8000')
});

app.get('/', ( req, res) => {
    res.status(200).send("The webhook is working.");
});

app.get('/webhook', (req, res) => {
    let mode = req.query["hub.mode"];
    let challenge = req.query["hub.challenge"];
    let token = req.query["hub.verify_token"];

    if(mode && token){
        if(mode === "subscribe" && token === mytoken){
            res.status(200).send(challenge);
        }else{
            res.status(403);  
        }
    }
});

const recentMessages = new Set();

app.post("/webhook",(req,res)=>{ 
    let body_param=req.body;
    if(body_param.object){
        if(body_param.entry &&
            body_param.entry[0].changes &&
            body_param.entry[0].changes[0].value &&
            body_param.entry[0].changes[0].value.messages &&
            body_param.entry[0].changes[0].value.messages[0] 
            ){
               let phone_no_id=body_param.entry[0].changes[0].value.metadata.phone_number_id;
               let from = body_param.entry[0].changes[0].value.messages[0].from; 
               let msg_body = body_param.entry[0].changes[0].value.messages[0].text.body;
               let messageId = body_param.entry[0].changes[0].value.messages[0].id;

               if (!recentMessages.has(messageId)) {
                recentMessages.add(messageId); 

                console.log("=====LOGS=====");
                console.log("Phone number: " + phone_no_id);
                console.log("From: " + from);
                console.log("Message body: " + msg_body);
                console.log("=====LOGS=====");

                axios.post(flaskRAGUrl, {
                    phone_number: from, 
                    user_query: msg_body 
                })
                .then(response => {
                    let flaskResponse = response.data.response;
                    console.log("=====LOGS=====");
                    console.log("RAG Response:", flaskResponse);
                    console.log("=====LOGS=====");
                    return axios.post(flaskDBUrl, {
                        phone_number: from,
                        user_query: msg_body,
                        rag_response: flaskResponse
                    }).then(() => {
                        return axios({
                            method: "POST",
                            url: "https://graph.facebook.com/v20.0/" + phone_no_id + "/messages?access_token=" + token,
                            data: {
                                messaging_product: "whatsapp",
                                to: from,
                                text: {
                                    body: flaskResponse,
                                }
                            },
                            headers: {
                                "Content-Type": "application/json"
                            }
                        });
                    });
                })
                .then(response => {
                    console.log("Message sent successfully:", response.data);
                    markMessageAsRead(phone_no_id, messageId, token);
                })
                .catch(error => {
                    console.error("Error communicating with Flask or sending message:", error);
                });

                res.sendStatus(200); 
            } else {
                console.log("Message already processed; ignoring.");
                res.sendStatus(200); 
            }
        }
        else {
            console.log("Received a status update, not a new message.");
            res.sendStatus(200);
        }
    } else {
        console.log("Not a valid WhatsApp webhook event.");
        res.sendStatus(400);
    }
});

const markMessageAsRead = (phone_no_id, messageId, token) => {
    axios({
        method: "POST",
        url: "https://graph.facebook.com/v20.0/"+phone_no_id+"/messages",
        data: {
            messaging_product: "whatsapp",
            status: "read",
            message_id: messageId
        },
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    }).then(response => {
        console.log("Message marked as read successfully:", response.data);
    }).catch(error => {
        console.error("Error marking message as read:", error);
    });
};


