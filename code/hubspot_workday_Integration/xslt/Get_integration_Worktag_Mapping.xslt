<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:bsvc="urn:com.workday/bsvc">
   <soapenv:Header>
      <bsvc:Workday_Common_Header>
         <!--Optional:-->
         <bsvc:Include_Reference_Descriptors_In_Response>true</bsvc:Include_Reference_Descriptors_In_Response>
      </bsvc:Workday_Common_Header>
      <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
        <wsse:UsernameToken xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
            <wsse:Username><xsl:value-of select="user"/>@<xsl:value-of select="tenant"/></wsse:Username>
            <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText"><xsl:value-of select="password"/></wsse:Password>
        </wsse:UsernameToken>
      </wsse:Security>
   </soapenv:Header>
   <soapenv:Body>
      <bsvc:Get_Integration_Worktag_Mappings_Request bsvc:version="v28.0">
         <!--Optional:-->
         <bsvc:Request_References>
            <!--1 or more repetitions:-->
            <bsvc:Integration_Worktag_Mapping_Reference bsvc:Descriptor="?">
               <!--Zero or more repetitions:-->
               <bsvc:ID bsvc:type="Integration_Worktag_Mapping_ID"><xsl:value-of select="mapping_name"/></bsvc:ID>
            </bsvc:Integration_Worktag_Mapping_Reference>
         </bsvc:Request_References>
      </bsvc:Get_Integration_Worktag_Mappings_Request>
   </soapenv:Body>
</soapenv:Envelope>
</xsl:template>
</xsl:stylesheet>