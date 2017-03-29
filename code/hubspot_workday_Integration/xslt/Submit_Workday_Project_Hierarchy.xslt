<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:bsvc="urn:com.workday/bsvc">
   <xsl:for-each select="root">
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
   <xsl:for-each select="hierarchy">
      <bsvc:Submit_Workday_Project_Hierarchy_Request bsvc:Add_Only="false" bsvc:version="v27.2">
         <bsvc:Project_Hierarchy_Reference bsvc:Descriptor="?">
            <bsvc:ID bsvc:type="Project_Hierarchy_ID"><xsl:value-of select="id"/></bsvc:ID>
         </bsvc:Project_Hierarchy_Reference>

         <bsvc:Project_Hierarchy_Data>
            <bsvc:Project_Hierarchy_Name><xsl:value-of select="name"/></bsvc:Project_Hierarchy_Name>


            <xsl:choose>
                <xsl:when test="enable_as_optional">
                    <bsvc:Enable_as_Optional_Hierarchy>true</bsvc:Enable_as_Optional_Hierarchy>
                    <xsl:for-each select="included_projects/item">
                    <bsvc:Included_Projects_in_Optional_Hierarchy_Reference bsvc:Descriptor="?">
                        <bsvc:ID bsvc:type="Project_ID"><xsl:value-of select="text()"/></bsvc:ID>
                    </bsvc:Included_Projects_in_Optional_Hierarchy_Reference>
                    </xsl:for-each>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:for-each select="included_projects/item">
                    <bsvc:Included_Projects_Reference bsvc:Descriptor="?">
                        <bsvc:ID bsvc:type="Project_ID"><xsl:value-of select="text()"/></bsvc:ID>
                    </bsvc:Included_Projects_Reference>
                    </xsl:for-each>
               </xsl:otherwise>
            </xsl:choose>

         </bsvc:Project_Hierarchy_Data>
      </bsvc:Submit_Workday_Project_Hierarchy_Request>
   </xsl:for-each>
   </soapenv:Body>
   </xsl:for-each>
</soapenv:Envelope>
</xsl:template>
</xsl:stylesheet>