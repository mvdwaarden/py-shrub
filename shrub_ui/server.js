// server.js
const express = require('express');
const fileUpload = require('express-fileupload');
const xml2js = require('xml2js');
const fs = require('fs');

const app = express();
app.use(fileUpload());
app.use(express.static('public'));

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/index.html');
});

app.post('/upload-xml', (req, res) => {
    if (!req.files || !req.files.xmlFile) {
        return res.status(400).send('No files were uploaded.');
    }

    if (false){
        const xmlFile = req.files.xmlFile;

        fs.readFile(xmlFile.tempFilePath, 'utf8', (err, data) => {
            if (err) {
                return res.status(500).send(err);
            }

            xml2js.parseString(data, (err, result) => {
                if (err) {
                    return res.status(500).send(err);
                }

                res.json(result);
            });
        });
    } else {
        res.json({
            "a": "ttt",
            "b" : "sss"
        });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
