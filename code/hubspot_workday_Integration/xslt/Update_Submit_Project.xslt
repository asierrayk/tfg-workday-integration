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
      <xsl:for-each select="project">
      <bsvc:Submit_Project_Request bsvc:Add_Only="false" bsvc:version="v27.2">
         <bsvc:Business_Process_Parameters>
            <bsvc:Auto_Complete>true</bsvc:Auto_Complete>
            <bsvc:Comment_Data>
               <bsvc:Comment>test</bsvc:Comment>
            </bsvc:Comment_Data>
         </bsvc:Business_Process_Parameters>
         <bsvc:Project_Reference bsvc:Descriptor="string">
         <!-- Zero or more repetitions: -->
         <bsvc:ID bsvc:type="Project_ID"><xsl:value-of select="id"/></bsvc:ID>
         </bsvc:Project_Reference>
         <bsvc:Project_Data>
            <bsvc:Project_Hierarchy_Reference bsvc:Descriptor="hierarchy">
               <bsvc:ID bsvc:type="Project_Hierarchy_ID"><xsl:value-of select="hierarchy"/></bsvc:ID>
            </bsvc:Project_Hierarchy_Reference>
            <bsvc:Project_Name><xsl:value-of select="name"/></bsvc:Project_Name>
            <bsvc:Project_Status_Reference bsvc:Descriptor="status">
               <bsvc:ID bsvc:type="Project_Status_ID"><xsl:value-of select="status"/></bsvc:ID>
            </bsvc:Project_Status_Reference>
            <bsvc:Start_Date><xsl:value-of select="start_date"/></bsvc:Start_Date>
         </bsvc:Project_Data>
      </bsvc:Submit_Project_Request>
      </xsl:for-each>
   </soapenv:Body>
   </xsl:for-each>
</soapenv:Envelope>
</xsl:template>
</xsl:stylesheet>