from django.shortcuts import render
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.permissions import AllowAny
from rest_framework import generics
from rest_framework.response import Response



class CollectionListHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="index.html")
    
class AboutPage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="about.html")
    
class SearchPage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="search.html")

class SignupPage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="signup.html")
    
class LoginPage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="login.html")

class UnauthorisedPage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="unauthorised.html")

class resetPassword(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="resetpassword.html")
    
    
class CollectionHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="collectionhome.html")

class CreateCollectionHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="createcollectionhome.html")
    
class EditCollectionHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="editcollectionhome.html")

class EditUserCollectionHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="editusercollectionhome.html")
    
class AddQuestionCollectionHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="addquestioncollectionhome.html")
    
    
class MediaHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="mediahome.html")
    
class CreateMediaHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="createmediahome.html")
    
class EditMediaHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="editmediahome.html")
    
class DeleteMediaHomePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="deletemediahome.html")

class UploadToArchive(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="uploadtest.html")

class CreateMediaAnnotatePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="createmediaannotatehome.html")
    
class DeleteMediaAnnotatePage(generics.GenericAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [AllowAny]
    
    def get(self,request,*args,**kwargs):
        return Response({},template_name="deletemediaannotatehome.html")
    