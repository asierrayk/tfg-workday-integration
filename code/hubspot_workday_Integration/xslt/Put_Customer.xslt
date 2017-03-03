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
      <xsl:for-each select="customer">
      <bsvc:Put_Customer_Request bsvc:Add_Only="true" bsvc:version="v27.2">
         <!--Optional:-->
         <!--<bsvc:Customer_Reference bsvc:Descriptor="?">-->
            <!--Zero or more repetitions:-->
            <!--<bsvc:ID bsvc:type="?">?</bsvc:ID>-->
         <!--</bsvc:Customer_Reference>-->
         <bsvc:Customer_Data>
            <!--Optional:-->
            <!--<bsvc:Customer_ID>test6</bsvc:Customer_ID>-->
            <!--Optional:-->
            <!--<bsvc:Customer_Reference_ID>test5</bsvc:Customer_Reference_ID>-->
            <bsvc:Customer_Name><xsl:value-of select="name"/></bsvc:Customer_Name>
            <!--Optional:-->
            <bsvc:Worktag_Only>false</bsvc:Worktag_Only>

            <bsvc:Customer_Category_Reference bsvc:Descriptor="category">
               <!--Zero or more repetitions:-->
               <bsvc:ID bsvc:type="Customer_Category_ID">GENERAL</bsvc:ID>
            </bsvc:Customer_Category_Reference>
            <!--<bsvc:Customer_Group_Reference bsvc:Descriptor="group">-->
               <!--Zero or more repetitions:-->
               <!--<bsvc:ID bsvc:type="Customer_Group_ID">BANKING</bsvc:ID>-->
            <!--</bsvc:Customer_Group_Reference>-->
            <!--<bsvc:Currency_Reference bsvc:Descriptor="currency">-->
               <!--Zero or more repetitions:-->
               <!--<bsvc:ID bsvc:type="Currency_ID">EUR</bsvc:ID>-->
            <!--</bsvc:Currency_Reference>-->

		  <bsvc:Business_Entity_Data>
               <bsvc:Business_Entity_Name><xsl:value-of select="name"/></bsvc:Business_Entity_Name>
            </bsvc:Business_Entity_Data>

            <bsvc:Customer_Status_Data>
               <bsvc:Customer_Status_Value_Reference bsvc:Descriptor="?">
                  <!--Zero or more repetitions:-->
                  <bsvc:ID bsvc:type="Business_Entity_Status_Value_ID">ACTIVE</bsvc:ID>
               </bsvc:Customer_Status_Value_Reference>
               <!--Optional:-->
               <!--<bsvc:Reason_for_Customer_Status_Change_Reference bsvc:Descriptor="?">-->
                  <!--Zero or more repetitions:-->
                  <!--<bsvc:ID bsvc:type="?">?</bsvc:ID>-->
               <!--</bsvc:Reason_for_Customer_Status_Change_Reference>-->
               <!--Optional:-->
               <!--<bsvc:Customer_Status_Change_Reason_Description>?</bsvc:Customer_Status_Change_Reason_Description>-->
            </bsvc:Customer_Status_Data>
         </bsvc:Customer_Data>
      </bsvc:Put_Customer_Request>
      </xsl:for-each>
   </soapenv:Body>
   </xsl:for-each>
</soapenv:Envelope>
</xsl:template>
</xsl:stylesheet>