<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:bsvc="urn:com.workday/bsvc">
<xsl:for-each select="root">
   <soapenv:Header>
      <bsvc:Workday_Common_Header>
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
      <bsvc:Put_Integration_Worktag_Mapping_Request bsvc:Add_Only="true" bsvc:version="v28.0">

         <bsvc:Integration_Worktag_Mapping_Data>
            <bsvc:ID><xsl:value-of select="mapping_name"/></bsvc:ID>
            <bsvc:Mapping_Name><xsl:value-of select="mapping_name"/></bsvc:Mapping_Name>
            <bsvc:Source_System_Reference bsvc:Descriptor="source">
               <bsvc:ID bsvc:type="Integration_Worktag_Mapping_Source_System_Name"><xsl:value-of select="source"/></bsvc:ID>
            </bsvc:Source_System_Reference>

            <bsvc:Mapping_Detail>
               <bsvc:External_Code><xsl:value-of select="external_code"/></bsvc:External_Code>
               <bsvc:Worktag_Reference bsvc:Descriptor="?">
                  <bsvc:ID bsvc:type="Project_ID"><xsl:value-of select="project_id"/></bsvc:ID>
               </bsvc:Worktag_Reference>
            </bsvc:Mapping_Detail>
         </bsvc:Integration_Worktag_Mapping_Data>
      </bsvc:Put_Integration_Worktag_Mapping_Request>
   </soapenv:Body>
</xsl:for-each>
</soapenv:Envelope>
</xsl:template>
</xsl:stylesheet>