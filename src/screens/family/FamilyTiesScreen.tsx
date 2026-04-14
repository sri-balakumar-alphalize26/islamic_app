import React from 'react';
import {View,Text,StyleSheet,TouchableOpacity,ScrollView} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {useTranslation} from 'react-i18next';
import {Ionicons} from '@expo/vector-icons';
import {COLORS} from '../../config';
export default function FamilyTiesScreen({navigation}:any){const{t}=useTranslation();
return(<SafeAreaView style={s.c}><View style={s.h}><TouchableOpacity onPress={()=>navigation.goBack()}><Ionicons name="arrow-back" size={24} color={COLORS.text}/></TouchableOpacity><Text style={s.title}>{t('family.title')}</Text><TouchableOpacity><Ionicons name="add-circle-outline" size={24} color={COLORS.primary}/></TouchableOpacity></View>
<ScrollView contentContainerStyle={s.body}><View style={s.empty}><Ionicons name="people-outline" size={48} color={COLORS.textTertiary}/><Text style={s.et}>No family members added yet</Text><Text style={s.es}>Add family members to track your connections and receive reminders to maintain Silat al-Rahim</Text><TouchableOpacity style={s.btn}><Text style={s.btnTxt}>{t('family.add_member')}</Text></TouchableOpacity></View></ScrollView></SafeAreaView>);}
const s=StyleSheet.create({c:{flex:1,backgroundColor:'#fff'},h:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',padding:16},title:{fontSize:17,fontWeight:'600',color:COLORS.text},body:{flexGrow:1,paddingHorizontal:24},empty:{flex:1,justifyContent:'center',alignItems:'center',paddingTop:80},et:{fontSize:17,fontWeight:'600',color:COLORS.text,marginTop:16},es:{fontSize:14,color:COLORS.textSecondary,textAlign:'center',marginTop:8,paddingHorizontal:20,lineHeight:22},btn:{backgroundColor:COLORS.primary,paddingHorizontal:24,paddingVertical:12,borderRadius:10,marginTop:24},btnTxt:{color:'#fff',fontWeight:'600',fontSize:15}});
