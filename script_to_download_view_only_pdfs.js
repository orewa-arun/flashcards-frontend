// Run this on the browser console to download the view only pdfs 
// after scrolling to the bottom of the page
(function() {
    // Create Trusted Types policy
    let policy;
    if (window.trustedTypes && trustedTypes.createPolicy) {
        policy = trustedTypes.createPolicy('jspdf-loader', {
            createScriptURL: (url) => url
        });
    }

    let jspdf = document.createElement("script");
    const scriptUrl = "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js";

    jspdf.onload = function () {
        const { jsPDF } = window.jspdf;
        let pdf = new jsPDF();
        let elements = document.getElementsByTagName("img");
        
        let addedImages = 0;
        for (let i = 0; i < elements.length; i++) {
            let img = elements[i];
            if (!/^blob:/.test(img.src)) {
                continue;
            }
            
            let canvasElement = document.createElement('canvas');
            let con = canvasElement.getContext("2d");
            canvasElement.width = img.width;
            canvasElement.height = img.height;
            con.drawImage(img, 0, 0, img.width, img.height);
            let imgData = canvasElement.toDataURL("image/jpeg", 1.0);
            
            if (addedImages > 0) {
                pdf.addPage();
            }
            pdf.addImage(imgData, 'JPEG', 0, 0, pdf.internal.pageSize.getWidth(), pdf.internal.pageSize.getHeight());
            addedImages++;
        }
        
        pdf.save("download.pdf");
    };

    jspdf.src = policy ? policy.createScriptURL(scriptUrl) : scriptUrl;
    document.body.appendChild(jspdf);
})();