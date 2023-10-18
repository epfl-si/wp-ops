import express, {RequestHandler} from "express";
import {AddressInfo} from "net";

export async function callAPIInTestServer(url: string, callBack: RequestHandler) {
    const testApp = express();
    testApp.get(url, callBack);

    const server = await testApp.listen();

    const port = (server.address() as AddressInfo).port;
    const response = await fetch(`http://localhost:${port}${url}`);
    console.log(`http://localhost:${port}`)
    return response;
}

export async function FakeServer() {
    const testApp = express();

    const server = await testApp.listen();

    const port = (server.address() as AddressInfo).port;

    function serve(url: string, callBack: RequestHandler) {
        testApp.get(url, callBack);
    }

    function baseURL() {
        return `http://localhost:${port}`
    }
    async function doRequest(url : string) : Promise<Response> {
        const response = await fetch(`${baseURL()}${url}`);
        return response;
    }
    async function stop(){
        server.close();
    }
    async function showUrlToStdout() {
        console.log(`Serving at ${baseURL()}`)
    }
    return { serve, doRequest, stop, showUrlToStdout, baseURL }
}